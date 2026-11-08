from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest
import sympy as sp

from contractive_tool.analysis.cauchy import (
    CauchyOptions, ExponentOptions, EtaTemplate, build_fixed_model, build_template_model,
    search_exponents, verify_exponent, automatic_t_grid)
from contractive_tool.analysis.cauchy_expressions import parse_expression
from contractive_tool.analysis.random_rounds import prepare_random_round
from contractive_tool.errors import AnalysisError
from contractive_tool.probability.fractional_moments import (
    FiniteLaw, power_enclosure, verify_power, certify_moment, verify_moment)

PROJECT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope='module')
def notes_round():
    return prepare_random_round(PROJECT/'examples/cauchy_notes.pp')


@pytest.mark.parametrize('base,k', [('0','3/2'), ('101','3/4'), ('17/100','3/4'),
                                  ('2','1/3'), ('1/100000000','1/7'), ('9/4','1/2')])
def test_exact_power_enclosures_and_tampering(base, k):
    w = power_enclosure(base, k)
    assert verify_power(w)
    assert sp.Rational(w['upper'])-sp.Rational(w['lower']) <= sp.Rational(1,10**12)
    bad = {**w, 'upper': '-1'}
    assert not verify_power(bad)


def test_joint_law_preserves_correlated_coordinates():
    r, s = sp.symbols('r s')
    law = FiniteLaw((r,s), (((-1,-1),sp.Rational(1,2)), ((1,1),sp.Rational(1,2))))
    norms = law.norm_atoms((r-s,))
    c = certify_moment(norms, sp.Rational(1,2))
    assert c['upper'] == '0' and verify_moment(c,norms)
    c['atoms'][0]['probability'] = '1/4'
    assert not verify_moment(c,norms)
    with pytest.raises(AnalysisError):
        FiniteLaw((r,), (((0,),1), ((1,),1))).validate()


def test_notes_round_uses_old_y_and_exact_decomposition(notes_round):
    r = notes_round
    x,y,z = sp.symbols('x y z')
    random = r.law.symbols[0]
    assert sp.expand(r.update[x]-x*((3+y)/10+(1+y)*10*random/20)) == 0
    assert r.update[y] == random and r.update[z] == 10*random
    numerator,q,b = r.decompose(x,(1,10*random))
    assert q == (x*y/10+3*x/10, x*y/20+x/20)
    assert sp.expand(numerator-sum(a*c for a,c in zip(q,b))) == 0
    with pytest.raises(AnalysisError,match='span'):
        r.decompose(x,(1,))
    with pytest.raises(AnalysisError,match='independent'):
        r.decompose(x,(1,random,2*random))


def test_samples_are_fresh_but_stored_values_are_reused(tmp_path):
    source = tmp_path/'samples.pp'
    source.write_text('x := 2; z := 0; while x >= 1 do '
        'z := Bernoulli(0.5); x := z; z := Bernoulli(0.5); x := x + z + z od; refute true;')
    r = prepare_random_round(source)
    a,b = r.law.symbols
    assert r.update[sp.Symbol('x')] == a+2*b
    assert len(r.law.atoms) == 4


def test_constant_probabilistic_branches_keep_probability_mass(tmp_path):
    source = tmp_path/'branches.pp'
    source.write_text('x := 2; while x >= 1 do if prob(0.99) then '
                      'x := 0.5*x else x := 100*x fi od; refute true;')
    r = prepare_random_round(source)
    z = r.law.symbols[0]
    assert r.law.atoms == (((0,),sp.Rational(99,100)), ((1,),sp.Rational(1,100)))
    numerator, q, basis = r.decompose(sp.Symbol('x'), (sp.Rational(1,2)+sp.Rational(199,2)*z,))
    assert q == (sp.Symbol('x'),)
    found, history = search_exponents(r.law.norm_atoms(basis), 1, 2,
                                     ExponentOptions(values=('1/2','1')))
    assert len(found) == 1 and found[0]['k'] == '1/2'
    assert sp.Rational(found[0]['decay_upper']) < sp.Rational(81,100)
    assert history[1]['status'] == 'no_contraction'


@pytest.mark.parametrize('program,reason', [
    ('x := Bernoulli(0.5); while x >= 1 do x := 0 od; refute true;', 'deterministic initialization'),
    ('x := 2; while x >= 1 do x := Uniform(0,1) od; refute true;', 'finite discrete'),
    ('x := 2; while x >= 1 do if prob(x) then x := 0 else x := 1 fi od; refute true;', None),
])
def test_unsupported_semantics_are_rejected(tmp_path, program, reason):
    source = tmp_path/'unsupported.pp'; source.write_text(program)
    with pytest.raises(AnalysisError,match=reason):
        prepare_random_round(source)


def test_state_model_independent_of_exponent_and_affine_in_unknowns(notes_round):
    r=notes_round; x,a,b=sp.symbols('x alpha beta'); basis=(1,10*r.law.symbols[0])
    one=CauchyOptions(exponents=ExponentOptions(values=('1',)))
    two=replace(one, exponents=ExponentOptions(values=('3/2',)))
    m1,_=build_fixed_model(r,x,basis=basis,options=one)
    m2,_=build_fixed_model(r,x,basis=basis,options=two)
    assert m1.to_data() == m2.to_data()
    template=EtaTemplate(a*x+b,(a,b),(a,b),(a+b-1,))
    m1,_=build_template_model(r,template,sp.Rational(1,2),basis=basis,options=one)
    m2,_=build_template_model(r,template,sp.Rational(1,2),basis=basis,options=two)
    assert m1.to_data() == m2.to_data() and m1.psd_blocks
    assert all(sp.Poly(e,*e.free_symbols).total_degree()<=1 for e in m1.equalities if e.free_symbols)
    with pytest.raises(AnalysisError,match='affine'):
        build_template_model(r,EtaTemplate(a*a*x,(a,)),sp.Rational(1,2),basis=basis)


def test_interval_search_covers_subunit_exponents_and_verified_bound(notes_round):
    opts=ExponentOptions(interval=('1/4','4'),coarse_points=16,refinements=1)
    values=opts.candidates()
    assert len(values)==31 and sp.Rational(3,2) in values and any(k<1 for k in values)
    norms=notes_round.law.norm_atoms((1,10*notes_round.law.symbols[0]))
    candidates,history=search_exponents(norms,sp.Rational(17,100),2,opts)
    c=next(c for c in candidates if c['k']=='3/2')
    assert sp.Rational(c['decay_upper']) < sp.Rational(7,20)
    assert verify_exponent(c,norms)
    bad=deepcopy(c); bad['decay_upper']='1/100'
    assert not verify_exponent(bad,norms)
    bad=deepcopy(c); bad['norm_power']['base']='1/100'
    assert not verify_exponent(bad,norms)
    grid=automatic_t_grid(norms,opts)
    assert len(grid)==8 and all(t>0 for t in grid)
    _,history=search_exponents(norms,grid[-1]**2,2,opts)
    assert any(row['status']=='proved' for row in history)


def test_expression_parser_supports_reserved_names_without_executing_code():
    x,beta=sp.symbols('x beta')
    assert parse_expression('beta*x + 0.1',(x,beta)) == beta*x+sp.Rational(1,10)
    for text in ('__import__("os")', 'x.__class__', 'x/y', 'sin(x)', 'x**1000'):
        with pytest.raises(AnalysisError):
            parse_expression(text,(x,beta))
