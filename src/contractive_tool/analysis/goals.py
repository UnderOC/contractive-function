"""Direct, time-independent polynomial certificates; no integer power lifting."""
from dataclasses import dataclass
from math import comb
import sympy as sp

from contractive_tool.analysis.templates import PolynomialTemplateFactory
from contractive_tool.expectation import ExpectationEngine
from contractive_tool.algebra import PolynomialService
from contractive_tool.errors import AnalysisError
from contractive_tool.positivity.ir import Implication


@dataclass
class PolynomialProblem:
    goal: str
    degree: int
    c: sp.Rational
    expressions: dict
    decisions: list
    objective: sp.Expr
    obligations: list
    context: dict | None = None

    def to_data(self):
        return {'goal':self.goal,'certificate_family':'polynomial','degree':self.degree,
                'c':str(self.c),'expressions':{l:str(v) for l,v in self.expressions.items()},
                'decisions':self.decisions,'objective':str(self.objective),
                'obligations':[o.to_data() for o in self.obligations], 'context':self.context}


def make_problem(cfg, evidence, degree, c, goal='tailbound', max_decisions=20000):
    if goal not in {'tailbound','assertion_violation'}:
        raise AnalysisError('Unknown analysis goal')
    if not 0<c<1:
        raise AnalysisError('Contraction factor must be strictly between 0 and 1')
    if cfg.failure_terminal is None:
        raise AnalysisError('A source assert/refute is required to define the failure event')
    ordinary = sorted(set(evidence.locations)-{cfg.normal_terminal,cfg.failure_terminal})
    count = len(ordinary)*comb(len(cfg.symbols.program_variables)+degree,degree)
    if count>max_decisions:
        raise AnalysisError('Template coefficient budget exceeded before basis expansion')
    factory = PolynomialTemplateFactory()
    template = factory.instantiate(cfg,degree=degree,prefix='v' if goal=='tailbound' else 'theta',locations=ordinary)
    expressions = {l:p.expression for l,p in template.expressions.items()}
    expressions[cfg.normal_terminal] = sp.Integer(0)
    expressions[cfg.failure_terminal] = sp.Integer(1)
    obligations = []
    for location in ordinary:
        for index,domain in enumerate(evidence.domains[location]):
            obligations.append(Implication(f'{location}_positive_{index}',domain,expressions[location],
                {'location':location},('nonnegative',)))
    service, expectation = PolynomialService(), ExpectationEngine()
    functions = {l:service.normalize(v) for l,v in expressions.items()}
    for group in cfg.transitions:
        if group.id not in evidence.group_domains:
            continue
        pre,traces = expectation.transition_expectation(functions,group)
        h = sp.expand(c*expressions[group.source]-pre.expression)
        for index,domain in enumerate(evidence.group_domains[group.id]):
            obligations.append(Implication(f'{group.id}_{index}',domain,h,
                {'location':group.source,'transition':group.id,'line':group.origin.start_line if group.origin else None},
                ('contraction','late_bad_exit' if goal=='tailbound' else 'prefixed_point')))
    initialized = expressions[evidence.start].subs(evidence.initial,simultaneous=True)
    objective = expectation.random_expectation(
        service.normalize(initialized), evidence.initial_random_model).expression
    if goal=='tailbound':
        # Restore the original program-entry clock after taking the exact
        # expectation of the symbolically executed initialization prefix.
        objective *= c**(-len(evidence.prefix))
    return PolynomialProblem(goal,degree,c,expressions,list(template.decisions),sp.expand(objective),obligations)
