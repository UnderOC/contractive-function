"""Exact diagonal coordinate changes for experiments, with CFG conjugacy checks.

Original coordinates x_i = scale_i * u_i. Variable names are retained in the
generated source. No guard, probability, control step, or event is approximated.
"""
from dataclasses import fields, is_dataclass, replace
from decimal import Decimal, localcontext
from pathlib import Path
import argparse
import hashlib
import json

import sympy as sp
from contractive_tool.algebra.polynomial import arithmetic_to_symbolic
from contractive_tool.frontend import ast
from contractive_tool.frontend.parser import parse_file
from contractive_tool.frontend.pretty import format_program
from contractive_tool.frontend.semantic import check_program
from contractive_tool.cfg.builder import build_cfg

ROOT = Path(__file__).resolve().parent


def number(value, span):
    value = sp.Rational(value)
    with localcontext() as ctx:
        ctx.prec = 200
        text = format(Decimal(int(value.p))/Decimal(int(value.q)), 'f')
    assert sp.Rational(text) == value, 'Coordinate conversion requires a finite decimal'
    return ast.Number(text, span)


def expression(value, span):
    value = sp.expand(value)
    if value.is_Rational:
        return number(value, span)
    if value.is_Symbol:
        return ast.Variable(str(value), span)
    if value.is_Add or value.is_Mul:
        args = [expression(a, span) for a in value.args]
        result = args[0]
        for arg in args[1:]:
            result = ast.Binary('+' if value.is_Add else '*', result, arg, span)
        return result
    if value.is_Pow and value.exp.is_Integer and value.exp > 0:
        base = expression(value.base, span)
        result = base
        for _ in range(int(value.exp)-1):
            result = ast.Binary('*', result, base, span)
        return result
    raise ValueError(value)


def transform(node, scales):
    substitution = {sp.Symbol(n): sp.Rational(v)*sp.Symbol(n) for n, v in scales.items()}
    if isinstance(node, (ast.Number, ast.Variable, ast.Unary, ast.Binary)):
        return expression(arithmetic_to_symbolic(node).subs(substitution, simultaneous=True), node.span)
    if isinstance(node, ast.Assign):
        if isinstance(node.value, ast.DistributionExpr):
            raise ValueError('Sample assignments need a separate distribution transformation')
        value = arithmetic_to_symbolic(node.value).subs(substitution, simultaneous=True)/scales[node.target]
        return replace(node, value=expression(value, node.span))
    if isinstance(node, ast.SourceSpan):
        return node
    if isinstance(node, tuple):
        return tuple(transform(item, scales) for item in node)
    if is_dataclass(node):
        return replace(node, **{f.name: transform(getattr(node, f.name), scales) for f in fields(node)})
    return node


def predicate_equal(original, scaled, substitution):
    assert type(original) is type(scaled)
    if isinstance(original, ast.Compare):
        assert original.operator == scaled.operator
        for name in ('left', 'right'):
            a = arithmetic_to_symbolic(getattr(original, name)).subs(substitution, simultaneous=True)
            b = arithmetic_to_symbolic(getattr(scaled, name))
            assert sp.expand(a-b) == 0
    elif isinstance(original, ast.BooleanConstant):
        assert original.value == scaled.value
    elif isinstance(original, ast.BoolUnary):
        assert original.operator == scaled.operator
        predicate_equal(original.operand, scaled.operand, substitution)
    elif isinstance(original, ast.BoolBinary):
        assert original.operator == scaled.operator
        predicate_equal(original.left, scaled.left, substitution)
        predicate_equal(original.right, scaled.right, substitution)
    else:
        raise ValueError(type(original))


def verify_conjugacy(original, scaled, scales):
    sub = {sp.Symbol(n):sp.Rational(v)*sp.Symbol(n) for n,v in scales.items()}
    assert original.initial_location == scaled.initial_location
    assert original.normal_terminal == scaled.normal_terminal
    assert original.failure_terminal == scaled.failure_terminal
    assert set(original.locations) == set(scaled.locations)
    for name, loc in original.locations.items():
        other = scaled.locations[name]
        assert loc.kind == other.kind
        predicate_equal(loc.invariant, other.invariant, sub)
    assert len(original.transitions) == len(scaled.transitions)
    branches = 0
    for a,b in zip(original.transitions, scaled.transitions):
        assert a.id == b.id and a.source == b.source
        predicate_equal(a.guard, b.guard, sub)
        assert len(a.branches) == len(b.branches)
        for left,right in zip(a.branches,b.branches):
            branches += 1
            assert left.destination == right.destination
            assert not left.update.samples and not right.update.samples
            assert sp.expand(arithmetic_to_symbolic(left.probability).subs(sub,simultaneous=True)
                             -arithmetic_to_symbolic(right.probability)) == 0
            assert set(left.update.assignments) == set(right.update.assignments)
            for name, expr in left.update.assignments.items():
                expected = arithmetic_to_symbolic(expr).subs(sub,simultaneous=True)/scales[name]
                assert sp.expand(expected-arithmetic_to_symbolic(right.update.assignments[name])) == 0
    return {'status':'proved','method':'exact_diagonal_CFG_conjugacy',
            'locations':len(original.locations),'transition_groups':len(original.transitions),'branches':branches}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args=parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    rows=[]
    for item in json.loads((ROOT/'inventory.json').read_text()):
        if item['family'] in ('Rdwalk','2DWalk','RdAdderLiteral'):
            continue
        source=ROOT/item['source']
        program=parse_file(source)
        cfg=build_cfg(check_program(program))
        family=item['family']
        scale = {'Race':100,'1DWalk':1000,'3DWalk':1000,'Prspeed':100,
                 'Newton':100,'Ref':100,'M1DWalk':100}[family]
        scales={name:1 if name=='alive' else scale for name in cfg.symbols.program_variables}
        dest=args.out/(item['id']+'.pp')
        converted=transform(program,scales)
        dest.write_text('/* Exact coordinates: original = scale * current. */\n'+format_program(converted))
        new_cfg=build_cfg(check_program(parse_file(dest)))
        check=verify_conjugacy(cfg,new_cfg,scales)
        rows.append({**item,'original_source':str(source.resolve()),'scaled_source':str(dest.resolve()),
            'original_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'scaled_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),
            'scales':scales,'equivalence_check':check})
    (args.out/'equivalence.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps({'converted':len(rows),'verified':len(rows)}))


if __name__=='__main__':
    main()
