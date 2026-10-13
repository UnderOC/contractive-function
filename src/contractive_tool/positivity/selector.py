from __future__ import annotations

import sympy as sp
from contractive_tool.errors import AnalysisError
from contractive_tool.positivity.base import EncodingLimits, match_coefficients, new_scalar
from contractive_tool.positivity.domains import eliminate_fixed_equalities, interval_features
from contractive_tool.positivity.ir import BasicSet, ConicModel


def prepare(obligation):
    domain, h = eliminate_fixed_equalities(obligation.domain, obligation.conclusion)
    if any(g.is_number and g < 0 for g in domain.generators) or any(
            e.is_number and e != 0 for e in domain.equalities):
        return domain, h, True
    generators = []
    for g in domain.generators:
        if g.is_number:
            continue
        _, primitive = sp.Poly(g, *domain.variables).primitive()
        g = primitive.as_expr()
        if g not in generators:
            generators.append(g)
    domain = BasicSet(domain.variables, tuple(generators), tuple(e for e in domain.equalities if e != 0))
    features = interval_features(domain)
    # In one dimension all affine constraints reduce exactly to strongest endpoints.
    if len(domain.variables) == 1 and features["affine_generators"]:
        x = domain.variables[0]
        lower, upper = features["bounds"][str(x)]
        generators = []
        if lower != "None":
            generators.append(x - sp.Rational(lower))
        if upper != "None":
            generators.append(sp.Rational(upper) - x)
        if lower != "None" and upper != "None":
            if sp.Rational(lower) > sp.Rational(upper):
                return domain, h, True
            if lower == upper:
                return BasicSet(()), h.subs(x, sp.Rational(lower)), False
        domain = BasicSet(domain.variables, tuple(generators))
    return domain, h, False


def build_plan(obligations, decisions, objective, registry, strategy="auto", order=2,
               handelman_degree=2, limits=None, fallback=True):
    limits = limits or EncodingLimits()
    if strategy != "auto" and strategy not in registry.known:
        raise AnalysisError("Unknown strategy ID")
    model = ConicModel(list(decisions), objective)
    if len(decisions) > limits.max_decisions:
        raise AnalysisError("Template decision count exceeds encoding budget")
    choices, features, skipped = [], {}, []
    for index, obligation in enumerate(obligations):
        variables = set(obligation.domain.variables)
        if any(g.free_symbols - variables for g in
               obligation.domain.generators + obligation.domain.equalities):
            raise AnalysisError("Domain generators must be fixed, without decision symbols")
        if obligation.conclusion.free_symbols - variables - {sp.Symbol(x) for x in decisions}:
            raise AnalysisError("Conclusion contains undeclared symbols")
        domain, h, empty = prepare(obligation)
        features[obligation.id] = interval_features(domain)
        namespace = f"o{index}"
        reserved = {str(x) for x in variables} | set(decisions)
        while any(name.startswith(namespace + '_') for name in reserved):
            namespace = '_' + namespace
        if empty or h == 0:
            chosen = "exact_empty_domain" if empty else "exact_identity"
        elif not domain.variables:
            slack = new_scalar(model, namespace + "_constant", nonnegative=True)
            match_coefficients(h - slack, (), model)
            chosen = "constant"
        else:
            preferred = ["handelman", "putinar", "schmudgen"] if strategy == "auto" else [strategy]
            if fallback:
                preferred += [name for name in registry.known if name not in preferred]
            chosen = None
            for name in preferred:
                plugin = registry.get(name)
                if plugin is None or not plugin.supports(domain):
                    skipped.append({"obligation_id": obligation.id, "strategy": name,
                                    "reason": registry.diagnostics.get(name, "unsupported_input")})
                    continue
                # Lower into a local fragment; a failed plugin cannot leave partial constraints behind.
                fragment = ConicModel([], sp.Integer(0))
                try:
                    plugin.lower(domain, h, fragment, namespace,
                                 handelman_degree if name == "handelman" else order, limits)
                except AnalysisError as error:
                    skipped.append({"obligation_id": obligation.id, "strategy": name,
                                    "reason": str(error)})
                    continue
                if len(model.decisions) + len(fragment.decisions) > limits.max_decisions:
                    raise AnalysisError("Complete model exceeds variable budget")
                model.decisions.extend(fragment.decisions)
                model.equalities.extend(fragment.equalities)
                model.nonnegative.extend(fragment.nonnegative)
                model.psd_blocks.extend(fragment.psd_blocks)
                chosen = name
                break
            if chosen is None:
                raise AnalysisError(f"No available strategy covers obligation {obligation.id}: {skipped[-3:]}")
        model.coverage[obligation.id] = {"origin": obligation.origin, "tags": obligation.tags,
                                        "strategy": chosen}
        choices.append({"obligation_id": obligation.id, "strategy": chosen,
                        "order": order, "handelman_degree": handelman_degree})
        if len(model.decisions) > limits.max_decisions:
            raise AnalysisError("Complete model exceeds variable budget")
    if len(model.coverage) != len(obligations):
        raise AnalysisError("Duplicate or missing obligation IDs")
    return model, {"choices": choices, "features": features, "skipped": skipped,
                   "registry": registry.snapshot(), "requested_strategy": strategy}
