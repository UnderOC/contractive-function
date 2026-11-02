"""Shared exact certificate recovery for polynomial analysis goals."""
from fractions import Fraction
import sympy as sp
from contractive_tool.analysis.semantics import prove_nonnegative
from .verification import reconstruct


def exact_template_check(problem, numerical_values):
    """Alternative certificate: rounded coefficients, original-domain exact identities.

    No time-indexed repair, sampling, or assumption that rounding preserves feasibility.
    """
    for denominator in (1000,1000000):
        values = {sp.Symbol(name):sp.Rational(Fraction(numerical_values[name]).limit_denominator(denominator))
                  for name in problem.decisions}
        proofs=[]
        for obligation in problem.obligations:
            conclusion=sp.expand(obligation.conclusion.xreplace(values))
            proof=prove_nonnegative(obligation.domain,conclusion)
            if proof is None:
                break
            proofs.append({'id':obligation.id,'proof':proof})
        else:
            bound=problem.objective.xreplace(values)
            if bound>=0:
                return {'status':'proved','method':'exact_original_domain_farkas',
                        'bound_exact':str(bound),'bound_numeric':float(bound),
                        'exact_values':{str(x):str(v) for x,v in values.items()},'obligations':proofs}
    return {'status':'solved_unverified','reason':'No exact original-domain certificate recovered'}


def certify_candidate(model, problem, values, *, options, deadline, bounded_reconstruction=False):
    """Same recovery sequence for tail and assertion; no solver status is a proof."""
    verified = reconstruct(model, values, deadline=deadline if bounded_reconstruction else None)
    audit = None
    if verified['status'] != 'proved' and options.repair_seconds > 0 and options.repair_max_solves > 0:
        from .repair import repair, RepairOptions
        repaired, audit = repair(model, values,
            options=RepairOptions(options.repair_seconds, options.repair_relative_gap, options.repair_max_solves),
            deadline=deadline, solver_seconds=options.per_attempt_seconds, verbose=options.verbose)
        audit['initial_verification'] = verified
        if repaired['status'] == 'proved':
            verified = repaired
    if verified['status'] != 'proved':
        fallback = exact_template_check(problem, values)
        fallback['gram_reconstruction'] = verified
        verified = fallback
    return verified, audit
