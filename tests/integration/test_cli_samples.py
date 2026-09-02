from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from contractive_tool.frontend.parser import parse_file
from contractive_tool.frontend.semantic import check_program


PROJECT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "sample, expected",
    [
        (
            "kelly_simple.pp",
            {"locations": 10, "transition_groups": 12, "branches": 13, "random_samples": 0},
        ),
        (
            "uniform_multiplicative.pp",
            {"locations": 7, "transition_groups": 9, "branches": 9, "random_samples": 1},
        ),
    ],
)
def test_actual_sample_runs_complete_cli_pipeline(
    tmp_path: Path, sample: str, expected: dict[str, int]
) -> None:
    out_dir = tmp_path / Path(sample).stem
    process = subprocess.run(
        ["contractive", "cfg", str(PROJECT / sample), "--out-dir", str(out_dir)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert process.returncode == 0, process.stderr
    summary = json.loads(process.stdout)
    assert summary["status"] == "ok"
    for key, value in expected.items():
        assert summary[key] == value

    expected_files = {
        "source.normalized.pp",
        "ast.json",
        "cfg.json",
        "cfg.txt",
        "cfg.dot",
        "validation.json",
        "manifest.json",
    }
    assert {path.name for path in out_dir.iterdir()} == expected_files
    cfg = json.loads((out_dir / "cfg.json").read_text(encoding="utf-8"))
    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    validation = json.loads((out_dir / "validation.json").read_text(encoding="utf-8"))
    assert cfg["initial_location"] in {location["id"] for location in cfg["locations"]}
    assert cfg["normal_terminal"] == "l_t"
    assert cfg["failure_terminal"] == "l_f"
    assert validation["valid"] is True
    assert manifest["phase"] == "frontend_pcfg"
    assert manifest["statistics"]["locations"] == expected["locations"]
    assert set(manifest["artifacts"]) == expected_files - {"manifest.json"}
    # The normalized artifact is itself valid source, not merely a debug dump.
    check_program(parse_file(out_dir / "source.normalized.pp"))


def test_parse_subcommand_writes_semantically_checked_ast(tmp_path: Path) -> None:
    output = tmp_path / "ast.json"
    process = subprocess.run(
        ["contractive", "parse", str(PROJECT / "kelly_simple.pp"), "--out", str(output)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert process.returncode == 0, process.stderr
    assert json.loads(output.read_text(encoding="utf-8"))["node"] == "Program"
