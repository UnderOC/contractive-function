from __future__ import annotations

import json
from pathlib import Path

import pytest
import sympy as sp

from contractive_tool.cfg.builder import build_cfg
from contractive_tool.errors import AnalysisError
from contractive_tool.frontend.parser import parse_file, parse_text
from contractive_tool.frontend.semantic import check_program
from contractive_tool.positivity.base import EncodingLimits
from contractive_tool.positivity.domains import predicate_regions
from contractive_tool.positivity.ir import BasicSet, ConicModel, Implication
from contractive_tool.positivity.registry import StrategyRegistry
from contractive_tool.positivity.selector import build_plan, prepare
from contractive_tool.backends.cvxpy.verification import exact_psd, reconstruct


PROJECT = Path(__file__).resolve().parents[2]


def graph(text):
    return build_cfg(check_program(parse_text(text)))


def obligation(h, domain=None):
    x = sp.Symbol("x")
    return Implication("positive", domain or BasicSet((x,), (x, 1-x)), h, {}, ("test",))


def test_strict_and_negated_predicates_use_covering_closure():
    cfg = graph("x := 1; assume not (x < 1 or x > 2);")
    pred = next(g.guard for g in cfg.transitions if cfg.locations[g.source].kind == "assume")
    regions = predicate_regions(pred, (sp.Symbol("x"),))
    assert len(regions) == 1
    assert set(regions[0].generators) == {sp.Symbol("x")-1, 2-sp.Symbol("x")}
    strict_cfg = graph("x := 0; assume x < 1;")
    strict = predicate_regions(next(g.guard for g in strict_cfg.transitions if strict_cfg.locations[g.source].kind == "assume"), (sp.Symbol("x"),))
    assert strict[0].generators == (1-sp.Symbol("x"),)


def test_exact_equality_elimination_and_empty_domain():
    x, y = sp.symbols("x y")
    domain, h, empty = prepare(obligation(x+y, BasicSet((x,y), (x, 1-x), (y-2,))))
    assert not empty and domain.variables == (x,) and h == x+2
    assert prepare(obligation(x, BasicSet((x,), (x-2, 1-x))))[2]


@pytest.mark.parametrize("strategy", StrategyRegistry.known)
def test_handcrafted_interval_certificate_compiles_and_roundtrips(strategy):
    x = sp.Symbol("x")
    model, plan = build_plan([obligation(x*(1-x))], [], sp.Integer(0),
                            StrategyRegistry(), strategy, order=2, handelman_degree=2,
                            fallback=False)
    assert plan["choices"][0]["strategy"] == strategy
    restored = ConicModel.from_data(json.loads(json.dumps(model.to_data())))
    assert restored.equalities == model.equalities
    assert restored.coverage.keys() == {"positive"}
    if strategy == "handelman":
        assert model.psd_blocks == []
    else:
        assert model.psd_blocks


def test_registry_missing_plugin_falls_back_without_dropping_obligations():
    x = sp.Symbol("x")
    registry = StrategyRegistry(enabled=("putinar",))
    model, plan = build_plan([obligation(1+x*x)], [], sp.Integer(0), registry,
                            "handelman", order=1, fallback=True)
    assert model.coverage.keys() == {"positive"}
    assert plan["choices"][0]["strategy"] == "putinar"
    assert any(row["strategy"] == "handelman" and row["reason"] == "disabled" for row in plan["skipped"])
    with pytest.raises(AnalysisError, match="No available strategy"):
        build_plan([obligation(x)], [], sp.Integer(0), registry, "handelman", fallback=False)


def test_absent_optional_module_uses_available_strategy(monkeypatch):
    import contractive_tool.positivity.registry as registry_module
    original_import = registry_module.import_module
    def with_missing_plugins(name):
        if name.endswith((".handelman", ".schmudgen")):
            raise ModuleNotFoundError(name)
        return original_import(name)
    monkeypatch.setattr(registry_module, "import_module", with_missing_plugins)
    x = sp.Symbol("x")
    model, plan = build_plan([obligation(1+x*x)], [], sp.Integer(0),
                            StrategyRegistry(), "auto", order=1)
    assert set(model.coverage) == {"positive"}
    assert plan["choices"][0]["strategy"] == "putinar"
    assert any("not_available" in row["reason"] for row in plan["skipped"])


def test_product_budget_is_checked_before_schmudgen_expansion():
    x = sp.Symbol("x")
    many = BasicSet((x,), tuple(x+i for i in range(15)))
    plugin = StrategyRegistry().get("schmudgen")
    with pytest.raises(AnalysisError, match="product count"):
        plugin.lower(many, x*x, ConicModel([], sp.Integer(0)), "o0", 1, EncodingLimits(max_products=16))


def test_exact_psd_rejects_indefinite_zero_diagonal_and_accepts_singular():
    assert exact_psd([[1,1],[1,1]])
    assert exact_psd([[0,0],[0,2]])
    assert not exact_psd([[0,1],[1,0]])
    assert not exact_psd([[1,2],[2,1]])


def test_rational_reconstruction_checks_equalities_nonnegativity_and_psd():
    a,b=sp.symbols("a b")
    model=ConicModel(["a","b"],a,[a+b-1], ["a","b"])
    result=reconstruct(model,{"a":0.333333333333,"b":0.666666666667})
    assert result["status"] == "proved" and result["bound_exact"] == "1/3"
    assert reconstruct(model,{"a":-1.,"b":2.})["status"] != "proved"
    assert reconstruct(model,{"a":float("nan"),"b":2.})["status"] == "verification_failed"
    q=ConicModel(["a","b"],a,[],[],[{"id":"Q","matrix":[["a","b"],["b","a"]]}])
    assert reconstruct(q,{"a":1.,"b":2.})["status"] != "proved"


def test_affine_model_rejects_unknown_products():
    a,b=sp.symbols("a b")
    with pytest.raises(ValueError,match="Non-affine"):
        ConicModel(["a","b"],a*b).to_data()


def test_zero_face_guesses_do_not_relax_exact_verification():
    a,b=sp.symbols('a b')
    # Numerical noise in a nearly zero block may be removed, but every original
    # rational constraint must still hold; contradictory equalities reject it.
    model=ConicModel(['a','b'],a,[a+b],['a','b'])
    recovered=reconstruct(model,{'a':2e-7,'b':3e-7})
    assert recovered['status']=='proved'
    assert recovered['exact_values']=={'a':'0','b':'0'}
    bad=ConicModel(['a','b'],a,[a+b+sp.Rational(1,10**8)],['a','b'])
    assert reconstruct(bad,{'a':2e-7,'b':3e-7})['status']!='proved'
