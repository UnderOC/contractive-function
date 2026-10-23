"""Symbolic, acyclic loop rounds over real polynomial invariant domains.

The certificate polynomial is nonnegative on the header invariant; only the
survival process is killed on exit. Sample-free rounds compose exact piecewise
survival expectations. Sampling retains the existing raw-moment sufficient rule.
Strict guards are pulled back before closing proof domains for the SOS backend.
"""
from dataclasses import dataclass
from math import comb

import sympy as sp

from contractive_tool.algebra import PolynomialService
from contractive_tool.algebra.polynomial import arithmetic_to_symbolic
from contractive_tool.analysis.goals import PolynomialProblem
from contractive_tool.analysis.guard_regions import GuardRegion, guard_regions
from contractive_tool.analysis.semantics import intersect
from contractive_tool.analysis.templates import PolynomialTemplateFactory
from contractive_tool.errors import AnalysisError
from contractive_tool.expectation import ExpectationEngine
from contractive_tool.positivity.ir import Implication


@dataclass
class SymbolicRoundKernel:
    cfg: object
    evidence: object
    entry: object
    variables: tuple
    round_lengths: tuple
    exit_lengths: tuple
    transitions: tuple
    max_cases: int = 256
    expectation_mode: str = 'exact_piecewise_survival'

    @property
    def header(self):
        return self.evidence.start

    def to_data(self):
        clock = {'unit':'completed_loop_iterations','prefix_steps':len(self.evidence.prefix),
                 'round_step_counts':list(self.round_lengths),'exit_step_counts':list(self.exit_lengths)}
        if len(self.round_lengths) == len(self.exit_lengths) == 1:
            clock['pcfg_relation'] = (f'T = {len(self.evidence.prefix)} + '
                                     f'{self.round_lengths[0]}*K + {self.exit_lengths[0]}')
        return {'status':'proved','method':'symbolic_acyclic_round_composition',
                'header':self.header,'variables':list(map(str,self.variables)),
                'domain':[d.to_data() for d in self.evidence.domains[self.header]],
                'entry_transition':self.entry.id,'transitions':list(self.transitions),
                'coverage':'all branches of the structured CFG; conditional cases checked separately',
                'invariant_evidence':'domain_evidence.json',
                'strict_guards':'exact through pullback; closed covering proof domains; no positive margin',
                'boundary':'polynomial nonnegative; survival process zero after exit',
                'expectation_mode':self.expectation_mode,
                'contraction':('piecewise killed expectation; closed-domain sufficient proof'
                               if self.expectation_mode == 'exact_piecewise_survival'
                               else 'raw round expectation dominates killed expectation'),
                'sampling_policy':'rounds with sampling retain raw moments; no truncated integration',
                'clock':clock}

    def preconditions(self, eta):
        """Return closed covering proof domains and their expectation polynomials."""
        return [(domain.closure(), value) for domain, value in self.partitioned_preconditions(eta)]

    def partitioned_preconditions(self, eta):
        """Return exact guard regions and weighted polynomial expectation cases."""
        cfg, variables = self.cfg, self.variables
        service, engine = PolynomialService(), ExpectationEngine()
        whole = GuardRegion(variables)
        cache = {}

        def pullback(domain, branch):
            updates = {sp.Symbol(n):arithmetic_to_symbolic(e) for n,e in branch.update.assignments.items()}
            return domain.substitute(updates)

        def group_cases(group):
            combined = [(whole,sp.Integer(0))]
            for branch in group.branches:
                if arithmetic_to_symbolic(branch.probability) == 0:
                    continue
                children = node_cases(branch.destination)
                pulled = [(region,engine.branch_expectation(service.normalize(value),branch).expression)
                          for domain,value in children if (region := pullback(domain,branch)) is not None]
                if len(combined)*len(pulled)>self.max_cases:
                    raise AnalysisError('Symbolic round case budget exceeded')
                combined = list(dict.fromkeys((region,sp.expand(x+y))
                    for a,x in combined for b,y in pulled if (region := a.intersect(b)) is not None))
            guards = guard_regions(group.guard,variables,max_regions=self.max_cases)
            if len(guards)*len(combined)>self.max_cases:
                raise AnalysisError('Symbolic round guard case budget exceeded')
            return list(dict.fromkeys((region,v) for g in guards for d,v in combined
                                     if (region := g.intersect(d)) is not None))

        def node_cases(location):
            if location == self.header:
                if self.expectation_mode == 'exact_piecewise_survival':
                    active = guard_regions(self.entry.guard,variables,max_regions=self.max_cases)
                    exited = guard_regions(self.entry.guard,variables,negated=True,max_regions=self.max_cases)
                    return [(d,eta) for d in active] + [(d,sp.Integer(0)) for d in exited]
                return [(whole,eta)]
            if location not in cache:
                cases = [case for group in cfg.outgoing(location) for case in group_cases(group)]
                if len(cases)>self.max_cases:
                    raise AnalysisError('Symbolic round case budget exceeded')
                cache[location] = cases
            return cache[location]

        return group_cases(self.entry)


def prepare_symbolic_round_kernel(cfg, evidence, *, max_nodes=4096, max_cases=256):
    header = evidence.start
    if cfg.locations[header].kind != 'while':
        raise AnalysisError('Symbolic rounds require initialization followed by a loop')
    terminals = {cfg.normal_terminal,cfg.failure_terminal}
    groups = cfg.outgoing(header)
    if len(groups) != 2:
        raise AnalysisError('Symbolic rounds require a structured binary loop guard')
    transitions = set()
    visited_count = 0

    def endpoints(location, seen):
        nonlocal visited_count
        visited_count += 1
        if visited_count>max_nodes:
            raise AnalysisError('Symbolic round graph budget exceeded')
        if location == header or location in terminals:
            return {(location,0)}
        if location in seen or cfg.locations[location].kind in {'while','assume'}:
            raise AnalysisError('Nested loops/cycles/assume are unsupported inside symbolic rounds or exit suffixes')
        outgoing = cfg.outgoing(location)
        if not outgoing:
            raise AnalysisError('Deadlocked symbolic round')
        result = set()
        for group in outgoing:
            transitions.add(group.id)
            for branch in group.branches:
                if arithmetic_to_symbolic(branch.probability) == 0:
                    continue
                result.update((dest,length+1) for dest,length in endpoints(branch.destination,seen|{location}))
        return result

    descriptions = []
    for group in groups:
        transitions.add(group.id)
        ends = set()
        for branch in group.branches:
            ends.update((dest,length+1) for dest,length in endpoints(branch.destination,set()))
        descriptions.append((group,ends))
    bodies = [(g,ends) for g,ends in descriptions if ends and all(dest==header for dest,_ in ends)]
    exits = [(g,ends) for g,ends in descriptions if ends and all(dest in terminals for dest,_ in ends)]
    if len(bodies)!=1 or len(exits)!=1:
        raise AnalysisError('Symbolic rounds require body paths returning to the header and a finite exit suffix')
    entry,body = bodies[0]
    # The new exact partitioning is scoped to finite probabilistic branches with
    # polynomial updates. Keep existing moment support for sampled rounds and
    # label its conservative expectation explicitly, rather than integrating a
    # sample-dependent indicator with unconditional moments.
    body_seen = set()
    def body_samples(group):
        if group.id in body_seen:
            return False
        body_seen.add(group.id)
        found = any(branch.update.samples for branch in group.branches)
        for branch in group.branches:
            if branch.destination != header:
                for child in cfg.outgoing(branch.destination):
                    found = body_samples(child) or found
        return found
    has_body_samples = body_samples(entry)
    kernel = SymbolicRoundKernel(cfg,evidence,entry,tuple(map(sp.Symbol,cfg.symbols.program_variables)),
                                 tuple(sorted({n for _,n in body})),tuple(sorted({n for _,n in exits[0][1]})),
                                 tuple(sorted(transitions)),max_cases)
    if has_body_samples:
        kernel.expectation_mode = 'raw_round_moments'
    # Domain composition does not depend on the template. Reject unsupported
    # sampled predicates before selecting this analysis route.
    kernel.preconditions(sp.Integer(0))
    return kernel


def make_symbolic_round_problem(cfg, kernel, degree, c, max_decisions=20000):
    if not 0<c<1:
        raise AnalysisError('Contraction factor must be strictly between 0 and 1')
    if comb(len(kernel.variables)+degree,degree)>max_decisions:
        raise AnalysisError('Template coefficient budget exceeded before basis expansion')
    template = PolynomialTemplateFactory().instantiate(cfg,degree=degree,prefix='eta',locations=(kernel.header,))
    eta = template.expressions[kernel.header].expression
    obligations = []
    origin = {'location':kernel.header,'kernel_evidence':'round_evidence.json'}
    for i,domain in enumerate(kernel.evidence.domains[kernel.header]):
        obligations.append(Implication(f'round_nonnegative_{i}',domain,eta,origin,('nonnegative','round_survival')))
    for i,domain in enumerate(kernel.evidence.group_domains[kernel.entry.id]):
        obligations.append(Implication(f'round_normalization_{i}',domain,eta-1,origin,('normalization','round_survival')))
    cases = kernel.partitioned_preconditions(eta)
    for i,(guard,pre) in enumerate(cases):
        for j,invariant in enumerate(kernel.evidence.domains[kernel.header]):
            obligations.append(Implication(f'round_contraction_{i}_{j}',intersect(invariant,guard.closure()),
                sp.expand(c*eta-pre),origin,('contraction','round_survival')))
    initialized = eta.subs(kernel.evidence.initial,simultaneous=True)
    objective = ExpectationEngine().random_expectation(initialized,kernel.evidence.initial_random_model).expression
    return PolynomialProblem('tailbound',degree,c,{kernel.header:eta},list(template.decisions),objective,obligations,
        {'rule':'round_survival','kernel':'symbolic','clock':kernel.to_data()['clock'],
         'event':'K > n','time_unit':'completed_loop_iterations',
         'boundary':'polynomial nonnegative; survival process zero after exit',
         'expectation_mode':kernel.expectation_mode,
         'round_preexpectations':[{'domain':d.closure().to_data(),'exact_domain':d.to_data(),
                                  'expression':str(p)} for d,p in cases]})
