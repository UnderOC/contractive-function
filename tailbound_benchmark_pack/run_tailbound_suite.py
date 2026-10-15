#!/usr/bin/env python3
"""Run the deterministic tail-bound benchmark instances with frozen budgets.

The solver artifact directory and the process log are deliberately separate:
``contractive_tool`` receives ``<output-root>/<stem>`` while this driver writes
captured stdout/stderr to ``<output-root>/logs/<stem>.run.log``.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time
from typing import Any, Sequence

from contractive_tool.analysis_pipeline import SearchOptions


@dataclass(frozen=True)
class Instance:
    benchmark_id: str
    stem: str
    pp_name: str


# This list is intentionally independent of manifest discovery.  The three
# nondeterministic benchmarks (09/10/11) are outside the runnable suite.
INSTANCES: tuple[Instance, ...] = (
    Instance("01_coupon2", "01_coupon2", "01_coupon2.pp"),
    Instance("02_coupon4", "02_coupon4", "02_coupon4.pp"),
    Instance("03_rw_int", "03_rw_int", "03_rw_int.pp"),
    Instance("04_rw_real", "04_rw_real", "04_rw_real.pp"),
    Instance("05_rdwalk_uniform", "05_rdwalk_uniform_d1", "05_rdwalk_uniform_d1.pp"),
    Instance("05_rdwalk_uniform", "05_rdwalk_uniform_d5", "05_rdwalk_uniform_d5.pp"),
    Instance("05_rdwalk_uniform", "05_rdwalk_uniform_d10", "05_rdwalk_uniform_d10.pp"),
    Instance("05_rdwalk_uniform", "05_rdwalk_uniform_d20", "05_rdwalk_uniform_d20.pp"),
    Instance("06_rw_real_large", "06_rw_real_large", "06_rw_real_large.pp"),
    Instance("07_polynomial_tail", "07_polynomial_tail", "07_polynomial_tail.pp"),
    Instance("08_escape_200", "08_escape_200", "08_escape_200.pp"),
    Instance(
        "12_signed_cost_multiplicative",
        "12_signed_cost_multiplicative",
        "12_signed_cost_multiplicative.pp",
    ),
)


# Freeze the current public defaults once per batch, avoiding stale copies of
# the degree policy and contraction search in the benchmark driver.
FROZEN_SEARCH_OPTIONS: dict[str, Any] = asdict(SearchOptions())

SUCCESS_STATUSES = frozenset({"proved", "no_certificate_found"})


def _positive_int(text: str) -> int:
    value = int(text)
    if value <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return value


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the 12 frozen deterministic .pp instances through the current "
            "tailbound solver. The output root must be absent or an empty directory."
        )
    )
    parser.add_argument(
        "--output-root",
        required=True,
        type=Path,
        help="new/nonexistent or existing empty root for artifacts, logs, and run_index.json",
    )
    parser.add_argument(
        "--jobs",
        type=_positive_int,
        default=1,
        help="maximum concurrent solver processes (default: 1)",
    )
    return parser


def _validated_sources(pack_dir: Path) -> dict[str, Path]:
    pp_dir = (pack_dir / "pp").resolve(strict=True)
    sources: dict[str, Path] = {}
    for instance in INSTANCES:
        source = (pp_dir / instance.pp_name).resolve(strict=True)
        if source.parent != pp_dir or not source.is_file():
            raise ValueError(f"invalid benchmark source: {instance.pp_name}")
        if instance.stem in sources:
            raise ValueError(f"duplicate frozen instance stem: {instance.stem}")
        sources[instance.stem] = source
    return sources


def _prepare_output_root(raw_root: Path, pp_dir: Path) -> tuple[Path, Path]:
    output_root = raw_root.expanduser().resolve()
    resolved_pp_dir = pp_dir.resolve(strict=True)
    if output_root == resolved_pp_dir or resolved_pp_dir in output_root.parents:
        raise ValueError("--output-root must not be the pp source directory or one of its descendants")

    if output_root.exists():
        if not output_root.is_dir():
            raise ValueError(f"--output-root is not a directory: {output_root}")
        if any(output_root.iterdir()):
            raise ValueError(f"--output-root must be empty: {output_root}")
    else:
        output_root.mkdir(parents=True)

    logs_dir = output_root / "logs"
    logs_dir.mkdir()
    for instance in INSTANCES:
        artifact_dir = output_root / instance.stem
        if artifact_dir.exists():
            raise ValueError(f"artifact path unexpectedly exists: {artifact_dir}")
    return output_root, logs_dir


def _solver_command(source: Path, artifact_dir: Path) -> list[str]:
    options = FROZEN_SEARCH_OPTIONS
    command = [
        sys.executable,
        "-m",
        "contractive_tool",
        "solve",
        str(source),
        "--goal",
        "tailbound",
        "--out-dir",
        str(artifact_dir),
        "--initial-degree",
        str(options["initial_degree"]),
        "--max-degree",
        str(options["max_degree"]),
        "--degree-step",
        str(options["degree_step"]),
        "--max-c-steps",
        str(options["max_c_steps"]),
        "--tail-rule",
        str(options["tail_rule"]),
        "--max-order",
        str(options["max_order"]),
        "--max-attempts-per-point",
        str(options["max_attempts_per_point"]),
        "--max-parameter-points",
        str(options["max_parameter_points"]),
        "--strategy",
        str(options["strategy"]),
        "--enabled-strategies",
        *options["enabled_strategies"],
        "--max-products",
        str(options["max_products"]),
        "--max-psd-dimension",
        str(options["max_psd_dimension"]),
        "--max-decisions",
        str(options["max_decisions"]),
        "--total-seconds",
        str(options["total_seconds"]),
        "--per-attempt-seconds",
        str(options["per_attempt_seconds"]),
        "--family",
        str(options["family"]),
    ]
    if options["c_values"] is not None:
        command.extend(["--c-values", *options["c_values"]])
    if options["continue_after_success"]:
        command.append("--continue-after-success")
    return command


def _write_run_log(
    path: Path,
    *,
    command: Sequence[str],
    cwd: Path,
    started_utc: str,
    finished_utc: str,
    elapsed_seconds: float,
    returncode: int | None,
    stdout: str,
    stderr: str,
    launch_error: str | None,
) -> None:
    metadata = {
        "command": list(command),
        "command_shell_escaped": shlex.join(command),
        "cwd": str(cwd),
        "started_utc": started_utc,
        "finished_utc": finished_utc,
        "elapsed_seconds": elapsed_seconds,
        "returncode": returncode,
        "launch_error": launch_error,
    }
    with path.open("x", encoding="utf-8", newline="") as handle:
        handle.write("===== RUN METADATA =====\n")
        json.dump(metadata, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n===== STDOUT BEGIN =====\n")
        handle.write(stdout)
        if stdout and not stdout.endswith("\n"):
            handle.write("\n")
        handle.write("===== STDOUT END =====\n")
        handle.write("===== STDERR BEGIN =====\n")
        handle.write(stderr)
        if stderr and not stderr.endswith("\n"):
            handle.write("\n")
        handle.write("===== STDERR END =====\n")


def _run_one(
    instance: Instance,
    source: Path,
    *,
    repo_root: Path,
    output_root: Path,
    logs_dir: Path,
    environment: dict[str, str],
) -> dict[str, Any]:
    artifact_dir = output_root / instance.stem
    log_path = logs_dir / f"{instance.stem}.run.log"
    command = _solver_command(source, artifact_dir)
    started_utc = _utc_now()
    started = time.monotonic()
    stdout = ""
    stderr = ""
    returncode: int | None = None
    launch_error: str | None = None

    try:
        completed = subprocess.run(
            command,
            cwd=repo_root,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="backslashreplace",
            check=False,
        )
        stdout = completed.stdout
        stderr = completed.stderr
        returncode = completed.returncode
    except OSError as error:
        launch_error = f"{type(error).__name__}: {error}"

    elapsed_seconds = time.monotonic() - started
    finished_utc = _utc_now()

    summary_path = artifact_dir / "summary.json"
    summary_status: str | None = None
    summary_error: str | None = None
    if summary_path.is_file():
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            status = summary.get("status")
            if not isinstance(status, str):
                raise ValueError("summary status is not a string")
            summary_status = status
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            summary_error = f"{type(error).__name__}: {error}"
    else:
        summary_error = "summary.json was not produced"

    _write_run_log(
        log_path,
        command=command,
        cwd=repo_root,
        started_utc=started_utc,
        finished_utc=finished_utc,
        elapsed_seconds=elapsed_seconds,
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
        launch_error=launch_error,
    )

    success = returncode == 0 and summary_status in SUCCESS_STATUSES
    return {
        "benchmark_id": instance.benchmark_id,
        "instance": instance.stem,
        "source": source.relative_to(repo_root).as_posix(),
        "source_sha256": _sha256(source),
        "artifact_dir": artifact_dir.relative_to(output_root).as_posix(),
        "summary": (
            summary_path.relative_to(output_root).as_posix() if summary_path.is_file() else None
        ),
        "run_log": log_path.relative_to(output_root).as_posix(),
        "command": command,
        "started_utc": started_utc,
        "finished_utc": finished_utc,
        "elapsed_seconds": elapsed_seconds,
        "returncode": returncode,
        "summary_status": summary_status,
        "summary_error": summary_error,
        "launch_error": launch_error,
        "success": success,
    }


def _write_index(path: Path, index: dict[str, Any]) -> None:
    with path.open("x", encoding="utf-8", newline="") as handle:
        json.dump(index, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    pack_dir = Path(__file__).resolve().parent
    repo_root = pack_dir.parent.resolve(strict=True)

    try:
        sources = _validated_sources(pack_dir)
        output_root, logs_dir = _prepare_output_root(args.output_root, pack_dir / "pp")
    except (OSError, ValueError) as error:
        parser.error(str(error))

    # Preserve the caller's solver/license environment without inspecting or
    # logging license variables, and suppress bytecode writes in child runs.
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"

    suite_started_utc = _utc_now()
    suite_started = time.monotonic()
    effective_jobs = min(args.jobs, len(INSTANCES))
    ordered_results: list[dict[str, Any] | None] = [None] * len(INSTANCES)

    with ThreadPoolExecutor(max_workers=effective_jobs) as executor:
        futures = {
            executor.submit(
                _run_one,
                instance,
                sources[instance.stem],
                repo_root=repo_root,
                output_root=output_root,
                logs_dir=logs_dir,
                environment=environment,
            ): position
            for position, instance in enumerate(INSTANCES)
        }
        for future in as_completed(futures):
            position = futures[future]
            instance = INSTANCES[position]
            try:
                result = future.result()
            except Exception as error:  # Preserve suite progress after an unexpected driver failure.
                result = {
                    "benchmark_id": instance.benchmark_id,
                    "instance": instance.stem,
                    "source": sources[instance.stem].relative_to(repo_root).as_posix(),
                    "source_sha256": _sha256(sources[instance.stem]),
                    "artifact_dir": instance.stem,
                    "summary": None,
                    "run_log": f"logs/{instance.stem}.run.log",
                    "returncode": None,
                    "summary_status": None,
                    "summary_error": None,
                    "launch_error": f"driver failure: {type(error).__name__}: {error}",
                    "success": False,
                }
            ordered_results[position] = result
            outcome = result.get("summary_status") or result.get("launch_error") or "failed"
            print(f"[{position + 1:02d}/{len(INSTANCES):02d}] {instance.stem}: {outcome}", flush=True)

    results = [result for result in ordered_results if result is not None]
    all_succeeded = len(results) == len(INSTANCES) and all(result["success"] for result in results)
    suite_elapsed_seconds = time.monotonic() - suite_started
    index = {
        "schema_version": 1,
        "status": "complete" if all_succeeded else "failed",
        "goal": "tailbound",
        "started_utc": suite_started_utc,
        "finished_utc": _utc_now(),
        "elapsed_seconds": suite_elapsed_seconds,
        "python_executable": sys.executable,
        "cwd": str(repo_root),
        "requested_jobs": args.jobs,
        "effective_jobs": effective_jobs,
        "search_options": FROZEN_SEARCH_OPTIONS,
        "instances": results,
    }
    _write_index(output_root / "run_index.json", index)
    print(f"run index: {output_root / 'run_index.json'}", flush=True)
    return 0 if all_succeeded else 1


if __name__ == "__main__":
    raise SystemExit(main())
