"""Restricted rational quadratic synthesis for the three M1DWalk experiments.

This supplements, and does not change the status of, the general SDP search.
Candidates are accepted only after replaying every original positivity and
full-first-moment obligation. Run with PYTHONPATH=src:reprsm_benchmark.
"""
from functools import lru_cache
from pathlib import Path
import argparse
import hashlib
import json

import sympy as sp

from recover_univariate import (
    BasicSet, Implication, arithmetic_to_symbolic, build_cfg, check_program,
    parse_file, prepare, prepare_program, verify_raw,
)


def construct(item, denominator):
    source = Path(item['scaled_source'])
    cfg = build_cfg(check_program(parse_file(source)))
    evidence = prepare_program(cfg)
    x, flag = sp.symbols('x alive')
    p = sp.Rational(item['parameters']['p'])
    c = 1-p/denominator
    delta = sp.Rational(1, 1000000)
    assert 0 < c < 1 and c**4 > 1-p
    # In normalized coordinates E[dx]=1/200, E[dx**2]=1/10000.
    # The rate is conservative; verification below is the acceptance criterion.
    rate = (c**4-(1-p))/((1-p)*sp.Rational(1, 200))*(1-10*p-10*delta)
    z = sp.Rational(99, 100)-x
    phi = (1-rate*z+rate**2*z**2/2)/c**2
    heads = [name for name, loc in cfg.locations.items() if loc.kind == 'while']
    if not heads:
        heads = [name for name in cfg.locations if name.startswith('L_while_')]
    assert len(heads) == 1, heads
    head = heads[0]

    def enabled(group, b):
        for domain in evidence.group_domains.get(group.id, []):
            restricted = BasicSet(domain.variables, domain.generators,
                                  domain.equalities+(flag-b,))
            _, _, empty = prepare(Implication('enabled', restricted, sp.Integer(1), {}, ()))
            if not empty:
                return True
        return False

    @lru_cache(None)
    def potential(loc, b):
        if loc == cfg.normal_terminal:
            return delta
        if loc == cfg.failure_terminal:
            return sp.Integer(1)
        if loc == head:
            return phi if b else delta/c**2
        groups = [g for g in cfg.outgoing(loc) if enabled(g, b)]
        if not groups:
            return delta
        assert len(groups) == 1
        value = sp.Integer(0)
        for branch in groups[0].branches:
            assert not branch.update.samples
            update = {sp.Symbol(n): arithmetic_to_symbolic(expr)
                      for n, expr in branch.update.assignments.items()}
            next_flag = update.get(flag, flag).subs(flag, b)
            assert next_flag in (0, 1)
            target = potential(branch.destination, int(next_flag))
            value += arithmetic_to_symbolic(branch.probability)*target.subs(update, simultaneous=True)
        return sp.expand(value/c)

    raw = {loc: sp.expand(flag*potential(loc, 1)+(1-flag)*potential(loc, 0))
           for loc in evidence.locations}
    checked = verify_raw(cfg, evidence, raw, c, delta)
    assert checked is not None, (item['id'], denominator)
    return {**checked, 'raw_polynomials': {k: str(v) for k, v in raw.items()},
            'source': str(source), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'degree': max(int(sp.Poly(v, x, flag).total_degree()) for v in raw.values()),
            'positivity_margin': str(delta),
            'candidate_family': 'quadratic_in_distance_with_exact_backward_CFG_propagation',
            'c_denominator': denominator, 'rate': str(rate), 'source_equivalence': item}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).parent/'refinement_20261109')
    args = parser.parse_args()
    out = args.root/'m1dwalk_constructive'
    out.mkdir(exist_ok=True)
    rows = []
    for item in json.loads((args.root/'scaled_inputs/equivalence.json').read_text()):
        if item['family'] != 'M1DWalk':
            continue
        candidates = []
        for denominator in (8, 100, 10000):
            result = construct(item, denominator)
            dest = out/f"{item['id']}_cden{denominator}.json"
            dest.write_text(json.dumps(result, indent=2)+'\n')
            row = {'case': item['id'], 'certificate': str(dest), 'denominator': denominator,
                   'status': result['status'], 'A': result['A_numeric'], 'c': result['c']}
            print(json.dumps(row), flush=True)
            rows.append(row)
            candidates.append(result)
        best = min(candidates, key=lambda r: sp.Rational(r['A_exact']))
        (out/f"{item['id']}.json").write_text(json.dumps(best, indent=2)+'\n')
    (out/'results.json').write_text(json.dumps(rows, indent=2)+'\n')


if __name__ == '__main__':
    main()
