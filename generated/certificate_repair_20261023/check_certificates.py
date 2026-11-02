"""Recheck saved certificates without invoking CVXPY or the repair code."""
import hashlib
import itertools
import json
from pathlib import Path

import sympy as sp


ROOT = Path(__file__).resolve().parent


def check(name):
    job = ROOT / name
    summary = json.loads((job/'summary.json').read_text())
    assert summary['status'] == 'proved'
    bound = summary['selection']
    path = job / bound['certificate']
    certificate = json.loads(path.read_text())
    verification = json.loads(path.with_name('verification.json').read_text())
    model = json.loads(path.with_name('conic_model.json').read_text())
    values = {k: sp.Rational(v) for k,v in verification['exact_values'].items()}
    assert set(values) == set(model['decisions'])

    def affine(row):
        return sp.Rational(row['constant']) + sum(sp.Rational(v)*values[k]
                                                  for k,v in row['coefficients'].items())

    assert all(affine(row) == 0 for row in model['coefficient_equalities'])
    assert all(values[k] >= 0 for k in model['nonnegative'])
    # All principal minors, using exact rational arithmetic, provide a separate
    # PSD check from the production Schur-complement verifier.
    minors = 0
    for block in model['psd_blocks']:
        matrix = sp.Matrix([[values[n] for n in row] for row in block['matrix']])
        assert matrix == matrix.T
        for size in range(1, matrix.rows+1):
            for indices in itertools.combinations(range(matrix.rows), size):
                assert matrix.extract(indices, indices).det() >= 0
                minors += 1
    A = affine(model['objective'])
    assert A == sp.Rational(verification['bound_exact']) == sp.Rational(bound['A_exact'])
    assert certificate['bound'] == bound
    assert A >= 0 and 0 < sp.Rational(bound['c']) < 1
    problem = json.loads((path.parent.parent.parent/'polynomial_problem.json').read_text())
    assert set(model['coverage']) == {o['id'] for o in problem['obligations']}
    substitution = {sp.Symbol(k): v for k,v in values.items()}
    symbols = {n:sp.Symbol(n) for o in problem['obligations'] for n in o['domain']['variables']}
    symbols.update({n:sp.Symbol(n) for n in values})
    for location, expression in problem['expressions'].items():
        assert sp.expand(sp.sympify(expression,locals=symbols).xreplace(substitution)
                         - sp.sympify(certificate['polynomials'][location],locals=symbols)) == 0
    if 'repair_stage' in verification:
        assert A <= sp.Rational(verification['repair_objective_cap'])
    manifest = json.loads((job/'manifest.json').read_text())
    for rel, digest in manifest['artifacts'].items():
        assert hashlib.sha256((job/rel).read_bytes()).hexdigest() == digest
    result = dict(status='passed', equalities=len(model['coefficient_equalities']),
                  nonnegative_scalars=len(model['nonnegative']), psd_blocks=len(model['psd_blocks']),
                  principal_minors=minors, A_exact=str(A), c=bound['c'],
                  repair_stage=verification.get('repair_stage'), manifest_hashes='passed')
    (ROOT/(name+'.independent_check.json')).write_text(json.dumps(result, indent=2)+'\n')
    print(name, result)


if __name__ == '__main__':
    for name in ('qlearning_fixed', 'qlearning_auto', 'kelly_auto'):
        check(name)
