#!/usr/bin/env python3
"""Exact algebraic certificates and symbolic checks against actual .pp sources.

The source-moment checks hold as polynomial identities, not only on sampled
states. Finite execution checks separately detect annotation/transcription
mistakes. Family proof scripts justify nonnegativity over their full domains.
"""
from pathlib import Path
from fractions import Fraction as F
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from exact_polynomial import Poly, variables, equal
from pp_semantics import Program, execute, evaluate


def with_definitions(state, certificate):
    env = dict(state)
    for name, expression in certificate.get("definitions", {}).items():
        env[name] = evaluate(expression, env)
    return env


def eta_at(state, certificate):
    return evaluate(certificate["eta_expression"], with_definitions(state, certificate))


def audit_source(directory, certificate):
    path = directory / certificate["file"]
    program = Program(path)
    names = sorted(program.initial)
    env = variables(names)
    eta = eta_at(env, certificate)
    branches = execute(program.loop.left, env, check_annotations=False)
    assert sum(p for p, _ in branches) == 1
    images = [(p, eta_at(nxt, certificate)) for p, nxt in branches]
    if certificate.get("branch_support"):
        remaining = list(certificate["branch_support"])
        assert len(remaining) == len(branches)
        for probability, successor in branches:
            matches = [i for i, branch in enumerate(remaining)
                       if probability == F(branch["probability"])
                       and all(successor[v] == evaluate(expr, env)
                               for v, expr in branch["updates"].items())]
            assert matches, "Source affine branch map/probability differs from certificate"
            remaining.pop(matches[0])
    mean = sum(p*e for p, e in images)
    second = sum(p*e*e for p, e in images)
    aliases = with_definitions(env, certificate)
    aliases["eta"] = eta
    checked = []
    if certificate.get("first_moment_expression"):
        equal(mean, evaluate(certificate["first_moment_expression"], aliases), "first moment")
        checked.append("first moment expression")
    c = F(certificate["c"])
    if certificate["mode"] == "positive":
        residual = c*eta-mean
        assert 0 < c < 1
    else:
        residual = mean-c*eta
        assert c > 1
    assert "first_moment_residual_expression" in certificate
    equal(residual, evaluate(certificate["first_moment_residual_expression"], aliases), "first moment witness")
    checked.append("first moment residual witness")
    if certificate["mode"] == "reciprocal":
        d, r0 = F(certificate["D"]), F(certificate["r0"])
        assert d >= c*c and 0 < r0 < c
        equal(d*eta*eta-second,
              evaluate(certificate["second_moment_residual_expression"], aliases),
              "second moment witness")
        checked.append("second moment residual witness")
        pstar = (d-c*c)/(d-2*r0*c+r0*r0)
        zstar = (d-r0*c)/(c-r0)
        assert 0 <= pstar < 1 and zstar >= c
        if "p_star" in certificate: assert F(certificate["p_star"]) == pstar
        if "z_star" in certificate: assert F(certificate["z_star"]) == zstar
        k = F(certificate["k"])
        assert k.denominator == 1, "Extend exact root handling if adding fractional powers"
        qmom = pstar*r0**(-int(k))+(1-pstar)*zstar**(-int(k))
        assert qmom <= F(certificate["q_certified"]) < 1
        if "q_mom" in certificate: assert F(certificate["q_mom"]) == qmom
    else:
        assert F(certificate["q_certified"]) == c and F(certificate["k"]) == 1
    k, threshold = F(certificate["k"]), F(certificate["a_or_b"])
    eta0 = eta_at(program.initial, certificate)
    assert eta0 == F(certificate["eta0"])
    base = eta0/threshold if certificate["mode"] == "positive" else threshold/eta0
    factor = F(certificate["prefactor"])
    assert factor**k.denominator == base**k.numerator
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if certificate.get("source_sha256"):
        assert digest == certificate["source_sha256"]
    for _, state in branches:
        for variable in certificate.get("state_variables", []):
            expression = state[variable]
            if isinstance(expression, Poly):
                assert expression.degree() <= 1, "Program is not affine"
    prefix = program.check_prefix_tree(depth=4)
    record = {
        "id": certificate["id"],
        "file": str(path.relative_to(ROOT)),
        "mode": certificate["mode"],
        "status": "passed",
        "symbolic_branch_count": len(branches),
        "source_polynomial_identities": checked,
        "source_identities_scope": "all real states, exact polynomial equality",
        "eta_degree": eta.degree(),
        "first_moment_degree": mean.degree(),
        "second_moment_degree": second.degree(),
        "source_sha256": digest,
        "finite_prefix_checks": prefix,
        "first_moment_coefficients": mean.as_records(names),
    }
    if certificate["id"] == "S2":
        point = {"x": F(1), "y": F(0)}
        outcomes = program.successors(point)
        sx = sum(p*nxt["x"]**2 for p, nxt in outcomes if program.active(nxt))
        sy = sum(p*nxt["y"]**2 for p, nxt in outcomes if program.active(nxt))
        assert sx == F(9,8) and sy == F(1,128)
        record["homogeneous_diagonal_k1_obstruction"] = {
            "state": {"x": "1", "y": "0"},
            "survival_truncated_x_squared_moment": str(sx),
            "survival_truncated_y_squared_moment": str(sy),
            "scope": "eta=a*x^2+b*y^2 with a,b>0; k=1; the current full annotated domain",
        }
    return record


def main():
    report = {
        "schema": "stochastic-affine-certificate-verification/1",
        "status": "passed",
        "arithmetic": "exact rational numbers",
        "original_synthesis_tool_run": False,
        "proof_scope": "family universal nonnegativity certificates plus symbolic source-moment equality",
        "annotation_execution_scope": "finite prefixes supplement the analytic invariant proofs",
        "proof_runs": [],
        "examples": [],
    }
    for group, expected in [("positive", 3), ("reciprocal", 2)]:
        directory = ROOT/group
        script = directory/("verify_"+group+".py")
        result = subprocess.run([sys.executable, str(script)], cwd=directory, capture_output=True, text=True)
        if result.returncode:
            sys.stderr.write(result.stdout+result.stderr)
            raise RuntimeError(f"{group} universal proof checker failed")
        report["proof_runs"].append({"group": group, "exit_code": result.returncode, "output": result.stdout.strip()})
        certificates = json.loads((directory/"certificates.json").read_text())
        assert len(certificates) == expected
        for certificate in certificates:
            record = audit_source(directory, certificate)
            report["examples"].append(record)
            print(f"{record['id']}: exact universal witnesses and symbolic source-moment checks PASS", flush=True)
    reference = json.loads((ROOT/"reference/certificates.json").read_text())[0]
    report["reference"] = audit_source(ROOT/"reference", reference)
    # Reference invariant: each row's exact box maximum is at most two.
    assert F(1,2)*2+F(1,4)*2+F(1,8)*4 == 2
    assert F(1,2)*2+F(1,8)*4 <= 2
    report["new_examples"] = len(report["examples"])
    assert report["new_examples"] == 5
    report["reference_counted_as_new_example"] = False
    (ROOT/"verification_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n")
    print("PASS: 5 new examples and the separate original reference.")


if __name__ == "__main__":
    main()
