from __future__ import annotations

import json
import subprocess
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]


def run_analysis(tmp_path: Path, arguments: list[str]):
    process = subprocess.run(
        ["contractive", "analyze", *arguments], text=True, capture_output=True, check=False
    )
    assert process.returncode == 0, process.stderr
    return json.loads(process.stdout)


def test_kelly_sample_cli_generates_exact_scalar_analysis_tree(tmp_path: Path) -> None:
    out = tmp_path / "kelly"
    result = run_analysis(
        tmp_path,
        [
            str(PROJECT / "kelly_simple.pp"),
            "--out-dir", str(out),
            "--analysis-id", "kelly_tail_3",
            "--goal", "tail_bound",
            "--certificate", "kelly",
            "--event", "wealth <= 0.6",
            "--horizon", "3",
            "--base", "wealth",
            "--lambda", "1/2",
            "--threshold", "0.6",
            "--initial", "wealth=1",
            "--initial", "round=0",
        ],
    )
    assert result["status"] == "proved"
    certificate = out / "analyses/kelly_tail_3/certificates/kelly"
    scalar = json.loads((certificate / "scalar_model.json").read_text(encoding="utf-8"))
    assert scalar["model_kind"] == "scalar_moment"
    assert scalar["parameters"]["lambda"] == "1/2"
    assert json.loads((out / "manifest.json").read_text())["backend"]["matlab_invoked"] is False
    assert (out / "shared/cfg.json").is_file()


def test_uniform_sample_cli_generates_assertion_obligations_with_moments(tmp_path: Path) -> None:
    out = tmp_path / "uniform"
    result = run_analysis(
        tmp_path,
        [
            str(PROJECT / "uniform_multiplicative.pp"),
            "--out-dir", str(out),
            "--analysis-id", "uniform_assertion",
            "--goal", "assertion_violation",
            "--certificate", "direct-theta",
            "--degree", "2",
            "--initial", "x=1",
            "--initial", "r=0",
        ],
    )
    assert result["status"] == "not_solved"
    certificate = out / "analyses/uniform_assertion/certificates/direct-theta"
    obligations = json.loads((certificate / "obligations.json").read_text(encoding="utf-8"))
    tags = {tag for item in obligations["obligations"] for tag in item["tags"]}
    assert {"failure_boundary", "normal_boundary", "nonnegative", "prefixed_point"} <= tags
    assert obligations["decision_coefficients_affine"] is True
    assert "4*theta_L_assign_1_5/3" in (certificate / "obligations.txt").read_text()
    assert not list(out.rglob("*.m"))
