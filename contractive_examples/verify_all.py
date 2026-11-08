#!/usr/bin/env python3
"""Run exact certificate witnesses and an independent check against .pp sources.

The family scripts check universal algebraic proof witnesses. Source checks here
exercise exact finite prefix trees and a rational grid; they detect transcription
errors but are deliberately NOT reported as proofs over all real states.
Requires Python 3.10+ standard library only.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import subprocess
import sys
from fractions import Fraction as F
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pp_semantics import Program, evaluate

ROOT = Path(__file__).resolve().parent
FAMILIES = ("kelly", "rcd", "qlearning")


def valid_invariant(program, state):
    return all(evaluate(expr, state) for expr in program.invariants)


def source_certificate_check(program, certificate, state):
    if not program.active(state):
        return 0
    expression = certificate.get("eta_expression", certificate["eta"])
    eta = evaluate(expression, state)
    threshold = F(certificate["a_or_b"])
    assert eta > 0, (certificate["id"], "eta is not positive", state)
    successors = program.successors(state)
    images = [(p, evaluate(expression, nxt)) for p, nxt in successors]
    mean = sum(p * e for p, e in images)
    mode = certificate["mode"]
    if mode == "positive":
        assert eta >= threshold, (certificate["id"], "guard lower bound", state)
        assert all(e >= 0 for p, e in images), (certificate["id"], "successor positivity", state)
        c = F(certificate.get("c", certificate["q_certified"]))
        assert mean <= c * eta, (certificate["id"], "positive drift", state, mean, c * eta)
    elif mode == "reciprocal":
        c, d, r0 = (F(certificate[t]) for t in ("c", "D", "r0"))
        assert eta <= threshold, (certificate["id"], "guard upper bound", state)
        assert mean >= c * eta, (certificate["id"], "reciprocal first moment", state, mean, c * eta)
        second = sum(p * e * e for p, e in images)
        assert second <= d * eta * eta, (certificate["id"], "reciprocal second moment", state, second, d * eta * eta)
        assert all(e >= r0 * eta for p, e in images), (certificate["id"], "support lower bound", state)
        if F(certificate["k"]) == 1:
            inverse_mean = sum(p * eta / e for p, e in images)
            assert inverse_mean <= F(certificate["q_certified"]), (certificate["id"], "inverse moment", state)
    else:
        raise ValueError(mode)
    return len(successors)


def check_parameters(program, certificate):
    k = F(certificate["k"])
    q = F(certificate["q_certified"])
    assert k > 0 and 0 < q < 1
    eta0 = evaluate(certificate.get("eta_expression", certificate["eta"]), program.initial)
    assert eta0 == F(certificate["eta0"]), (certificate["id"], "initial eta mismatch")
    threshold = F(certificate["a_or_b"])
    base = eta0 / threshold if certificate["mode"] == "positive" else threshold / eta0
    factor = F(certificate.get("prefactor", certificate.get("initial_factor")))
    assert factor ** k.denominator == base ** k.numerator
    if certificate.get("source_sha256"):
        assert certificate["source_sha256"] == hashlib.sha256(program.path.read_bytes()).hexdigest()
    if certificate["mode"] == "reciprocal":
        c, d, r0 = (F(certificate[t]) for t in ("c", "D", "r0"))
        assert c > 1 and 0 < r0 < c and d >= c * c
        p = (d-c*c) / (d-2*r0*c+r0*r0)
        z = (d-r0*c) / (c-r0)
        assert 0 <= p < 1 and z >= c
        assert p == F(certificate["p_star"])
        assert z == F(certificate["z_star"])
        if k.denominator == 1:
            computed_q = p * r0 ** (-int(k)) + (1-p) * z ** (-int(k))
            assert computed_q <= q, (certificate["id"], "q_mom mismatch", computed_q, q)
        elif certificate["id"] == "K3":
            # Here the two-point law is exactly {.4,1.6}; at k=1/2 q²=9/10.
            assert (p, r0, z, k) == (F(1,5), F(2,5), F(8,5), F(1,2))
            assert F(9,10) < q*q < 1
        else:
            raise AssertionError("No exact noninteger q check registered")


def inspect_source(program, certificate, family, depth=4):
    check_parameters(program, certificate)
    frontier = {tuple(sorted(program.initial.items()))}
    visited = set()
    branch_count = 0
    active_count = 0
    for _ in range(depth):
        new = set()
        for frozen in frontier:
            state = dict(frozen)
            program.check_invariant(state)
            if program.active(state):
                active_count += 1
                branch_count += source_certificate_check(program, certificate, state)
                new.update(tuple(sorted(nxt.items())) for _, nxt in program.successors(state))
            visited.add(frozen)
        frontier = new
    if family == "kelly":
        values = [F(i, 8) for i in range(0, 33)]
    elif family == "qlearning":
        values = [F(i, 8) for i in range(0, 13)]
    else:
        values = [F(i, 4) for i in range(-12, 13)]
    names = sorted(program.initial)
    grid_count = 0
    grid_branches = 0
    for point in itertools.product(values, repeat=len(names)):
        state = dict(zip(names, point))
        frozen = tuple(sorted(state.items()))
        if frozen in visited or not valid_invariant(program, state) or not program.active(state):
            continue
        grid_branches += source_certificate_check(program, certificate, state)
        grid_count += 1
    return {
        "id": certificate["id"],
        "file": str(program.path.relative_to(ROOT)),
        "mode": certificate["mode"],
        "status": "passed",
        "prefix_depth": depth,
        "active_prefix_states": active_count,
        "prefix_branch_transitions": branch_count,
        "additional_rational_grid_states": grid_count,
        "grid_branch_transitions": grid_branches,
        "metadata_and_moment_parameters": "exact rational checks passed",
        "source_sha256": hashlib.sha256(program.path.read_bytes()).hexdigest(),
    }


def main():
    report = {
        "status": "passed",
        "arithmetic": "exact fractions; no binary floating point in checks",
        "universal_proofs": "family algebraic witness scripts plus family README derivations",
        "source_check_scope": "exact finite prefixes and rational grids; not a universal reachability proof",
        "original_synthesis_tool_run": False,
        "family_proof_runs": [],
        "examples": [],
    }
    for family in FAMILIES:
        checker = ROOT / family / ("verify_" + family + ".py")
        completed = subprocess.run([sys.executable, str(checker)], cwd=checker.parent, capture_output=True, text=True)
        if completed.returncode:
            sys.stderr.write(completed.stdout + completed.stderr)
            raise RuntimeError(f"{family} proof checker failed")
        report["family_proof_runs"].append({"family": family, "exit_code": completed.returncode, "output": completed.stdout.strip()})
        print(f"{family}: algebraic witnesses PASS", flush=True)
        certificates = json.loads((ROOT / family / "certificates.json").read_text())
        assert len(certificates) == 5
        for certificate in certificates:
            program = Program(ROOT / family / certificate["file"])
            record = inspect_source(program, certificate, family)
            report["examples"].append(record)
            print(f"  {certificate['id']}: source/annotation/moment checks PASS ({record['additional_rational_grid_states']} extra rational states)", flush=True)
    report["total_examples"] = len(report["examples"])
    report["positive_examples"] = sum(e["mode"] == "positive" for e in report["examples"])
    report["reciprocal_examples"] = sum(e["mode"] == "reciprocal" for e in report["examples"])
    report["total_source_branch_transitions"] = sum(e["prefix_branch_transitions"] + e["grid_branch_transitions"] for e in report["examples"])
    output = ROOT / "verification_report.json"
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(f"PASS: {report['total_examples']} examples; {report['total_source_branch_transitions']} exact source branch transitions checked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
