import pytest
import sympy as sp
from contractive_tool.analysis.goals import make_problem
from contractive_tool.analysis.degree_policy import DegreePolicy
from contractive_tool.analysis.certificate_families import FractionalPowerFamily
from contractive_tool.analysis.semantics import prepare_program
from contractive_tool.cfg.builder import build_cfg
from contractive_tool.errors import AnalysisError
from contractive_tool.frontend.parser import parse_text
from contractive_tool.frontend.semantic import check_program


def graph(source):
    return build_cfg(check_program(parse_text(source)))


def test_direct_degree_prefix_clock_and_affine_coefficients():
    cfg=graph('x := 4; {x >= 0} while x >= 1 do {x >= 1} x := x * 0.5 od; refute true;')
    evidence=prepare_program(cfg)
    c=sp.Rational(9,10)
    problem=make_problem(cfg,evidence,2,c)
    assert len(evidence.prefix)==1
    assert problem.objective == problem.expressions[evidence.start].subs({'x':4})/c
    unknowns=[sp.Symbol(n) for n in problem.decisions]
    assert all(sp.Poly(o.conclusion,*unknowns).total_degree()<=1 for o in problem.obligations)
    assert problem.expressions[cfg.normal_terminal]==0
    assert problem.expressions[cfg.failure_terminal]==1
    assert all(cfg.locations[o.origin['location']].kind not in {'normal_terminal','failure_terminal'}
               for o in problem.obligations)
    assertion=make_problem(cfg,evidence,2,c,'assertion_violation')
    assert assertion.objective == assertion.expressions[evidence.start].subs({'x':4})
    assert any('prefixed_point' in o.tags for o in assertion.obligations)


def test_degree_schedule_and_fractional_extension():
    assert list(DegreePolicy().degrees())==[1,2,3,4,5,6]
    assert list(DegreePolicy(2,6,2).degrees())==[2,4,6]
    with pytest.raises(AnalysisError): list(DegreePolicy(3,2).degrees())
    with pytest.raises(AnalysisError,match='fractional'): FractionalPowerFamily().instantiate()


def test_invalid_invariant_is_rejected_before_synthesis():
    cfg=graph('x := 1; {x >= 0} while x >= 0 do {x >= 0} x := x - 1 od; refute true;')
    with pytest.raises(AnalysisError,match='inductive invariant'):
        prepare_program(cfg)


def test_false_initial_invariant_and_missing_initial_value_rejected():
    with pytest.raises(AnalysisError,match='Initial control'):
        prepare_program(graph('x := 1; {x = 0} while x > 0 do skip od; refute true;'))
    with pytest.raises(AnalysisError,match='initialize'):
        prepare_program(graph('while x > 0 do x := x - 1 od; refute true;'))


def test_nonterminating_loop_is_not_assumed_to_exit():
    cfg=graph('x := 0; while true do skip od; refute true;')
    evidence=prepare_program(cfg)
    problem=make_problem(cfg,evidence,2,sp.Rational(1,2))
    # No termination premise and no finite-horizon domain enumeration.
    assert any('contraction' in o.tags for o in problem.obligations)
    assert all(not o.domain.generators for o in problem.obligations)


def test_random_initialization_uses_exact_independent_prefix_expectation():
    cfg=graph('''
        random r ~ Uniform(0, 2);
        x := r;
        y := r;
        {x >= 0 and x <= 2 and y >= 0 and y <= 2}
        refute true;
    ''')
    evidence=prepare_program(cfg)
    assert len(evidence.prefix)==2
    assert len(evidence.initial_random_model.symbols)==2
    assert evidence.initial[sp.Symbol('x')] != evidence.initial[sp.Symbol('y')]
    c=sp.Rational(1,2)
    problem=make_problem(cfg,evidence,2,c)
    x,y=sp.symbols('x y')
    polynomial=sp.Poly(problem.expressions[evidence.start],x,y)
    expected=sum((coefficient * sp.Rational(2)**x_power / (x_power+1)
                  * sp.Rational(2)**y_power / (y_power+1)
                  for (x_power,y_power),coefficient in polynomial.terms()),sp.Integer(0))/c**2
    assert sp.expand(problem.objective-expected)==0


def test_random_initialization_checks_the_whole_continuous_support():
    evidence=prepare_program(graph(
        'x := Uniform(0, 2); {x >= 0 and x <= 2} refute true;'))
    assert evidence.initial_support[0].generators == (
        sp.Symbol('__initial_sample_1'), 2-sp.Symbol('__initial_sample_1'))
    with pytest.raises(AnalysisError,match='initialization support'):
        prepare_program(graph('x := Uniform(-1, 1); {x >= 0} refute true;'))


def test_internal_distribution_support_proves_invariants_and_rejects_bad_ones():
    continuous=prepare_program(graph('''
        x := 0; y := 0; z := 0;
        {x = y} while x <= 0 do
            {x = y} z := Uniform(-1, 1);
            {x = y} x := x + z;
            {x = y + z} y := y + z
        od;
        refute true;
    '''))
    random_proofs=[row for row in continuous.proofs if row.get('random_samples')]
    assert len(random_proofs)==1
    assert random_proofs[0]['random_samples'][0] == {
        'symbol':'__sample_z_1','distribution':'Uniform','arguments':['-1','1']}
    support=random_proofs[0]['proofs'][0]['support_domain']
    assert support['generators']==['__sample_z_1 + 1','1 - __sample_z_1']
    assert support['equalities']==['x - y']

    discrete=prepare_program(graph('''
        x := 0;
        {x = 0 or x = 1} while x < 2 do x := Bernoulli(0.5) od;
        refute true;
    '''))
    bernoulli_proof=next(row for row in discrete.proofs if row.get('random_samples'))
    assert len(bernoulli_proof['proofs'])==2
    assert {tuple(row['support_domain']['equalities'])
            for row in bernoulli_proof['proofs']} == {
                ('__sample_x_1',), ('__sample_x_1 - 1',)}

    with pytest.raises(AnalysisError,match='random support region'):
        prepare_program(graph('''
            x := 0;
            {x >= 0} while x < 1 do x := Normal(0, 1) od;
            refute true;
        '''))


def test_deterministic_if_branch_kind_is_supported():
    evidence=prepare_program(graph(
        'x := 0; if x >= 0 then x := 1 else x := 2 fi; refute true;'))
    assert any(location.startswith('L_branch_') for location in evidence.locations)
