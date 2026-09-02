from __future__ import annotations

import hashlib
import json
import platform
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from contractive_tool import __version__
from contractive_tool.cfg.builder import build_cfg
from contractive_tool.cfg.dot_writer import cfg_to_dot
from contractive_tool.cfg.json_writer import cfg_to_data
from contractive_tool.cfg.text_writer import cfg_to_text
from contractive_tool.cfg.validation import validate_cfg
from contractive_tool.frontend.ast import ast_to_data
from contractive_tool.frontend.parser import parse_file
from contractive_tool.frontend.pretty import format_program
from contractive_tool.frontend.semantic import check_program


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, content: object) -> None:
    _write_text(path, json.dumps(content, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


def compile_to_cfg(source: str | Path, out_dir: str | Path) -> dict[str, object]:
    """Run the complete observable frontend and write all shared pCFG artifacts."""
    source_path = Path(source).resolve()
    output_path = Path(out_dir).resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    parsed = parse_file(source_path)
    program = check_program(parsed)
    cfg = build_cfg(program)
    validation = validate_cfg(cfg)

    artifacts = {
        "source.normalized.pp": format_program(program.ast),
        "ast.json": json.dumps(
            ast_to_data(program.ast), indent=2, sort_keys=True, ensure_ascii=False
        )
        + "\n",
        "cfg.json": json.dumps(cfg_to_data(cfg), indent=2, sort_keys=True, ensure_ascii=False)
        + "\n",
        "cfg.txt": cfg_to_text(cfg),
        "cfg.dot": cfg_to_dot(cfg),
        "validation.json": json.dumps(
            asdict(validation), indent=2, sort_keys=True, ensure_ascii=False
        )
        + "\n",
    }
    for name, content in artifacts.items():
        _write_text(output_path / name, content)

    distribution_records = []
    for group in cfg.transitions:
        for branch in group.branches:
            for sample in branch.update.samples:
                distribution_records.append(
                    {
                        "transition_id": group.id,
                        "symbol": sample.symbol,
                        "distribution": ast_to_data(sample.distribution),
                        "fresh": sample.fresh,
                    }
                )
    artifact_hashes = {name: _sha256(output_path / name) for name in sorted(artifacts)}
    manifest = {
        "schema_version": 1,
        "tool": {"name": "contractive-tool", "version": __version__},
        "python_version": platform.python_version(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input": {"path": str(source_path), "sha256": _sha256(source_path)},
        "phase": "frontend_pcfg",
        "semantics": {
            "updates": "simultaneous within a transition; source statements remain sequential",
            "random_sampling": program.sampling_semantics,
            "random_independence": program.independence_assumption,
            "normal_terminal": cfg.normal_terminal,
            "failure_terminal": cfg.failure_terminal,
            "refute": "predicate true transitions to failure terminal",
            "strict_inequalities": "preserved exactly in pCFG guards; no SOS margin applied",
        },
        "random_samples": distribution_records,
        "statistics": {
            "locations": len(cfg.locations),
            "transition_groups": len(cfg.transitions),
            "branches": sum(len(group.branches) for group in cfg.transitions),
            "program_variables": len(cfg.symbols.program_variables),
            "random_samples": len(distribution_records),
            "probability_obligations": len(validation.probability_obligations),
        },
        "artifacts": artifact_hashes,
    }
    _write_json(output_path / "manifest.json", manifest)

    return {
        "source": str(source_path),
        "out_dir": str(output_path),
        "initial_location": cfg.initial_location,
        "normal_terminal": cfg.normal_terminal,
        "failure_terminal": cfg.failure_terminal,
        **manifest["statistics"],
    }

