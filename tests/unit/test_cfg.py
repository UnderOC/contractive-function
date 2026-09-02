from __future__ import annotations

from contractive_tool.cfg.builder import build_cfg
from contractive_tool.cfg.json_writer import cfg_to_data
from contractive_tool.cfg.validation import validate_cfg
from contractive_tool.frontend.ast import BoolUnary, Number, Variable, format_expr
from contractive_tool.frontend.parser import parse_text
from contractive_tool.frontend.semantic import check_program


def cfg(source: str):
    result = build_cfg(check_program(parse_text(source, "cfg.pp")))
    validate_cfg(result)
    return result


def location_of_kind(graph, kind: str):
    return next(location for location in graph.locations.values() if location.kind == kind)


def test_sequence_updates_have_distinct_locations_and_continuation() -> None:
    graph = cfg("x := 1; y := x + 1;")
    first = graph.locations[graph.initial_location]
    assert first.kind == "assign"
    first_destination = graph.outgoing(first.id)[0].branches[0].destination
    assert graph.locations[first_destination].kind == "assign"
    assert graph.outgoing(first_destination)[0].branches[0].destination == graph.normal_terminal


def test_deterministic_if_has_complementary_guard_groups() -> None:
    graph = cfg("x := 0; if x < 1 then x := 2; else x := 3; fi;")
    branch = location_of_kind(graph, "branch")
    groups = graph.outgoing(branch.id)
    assert len(groups) == 2
    assert isinstance(groups[1].guard, BoolUnary)
    assert groups[1].guard.operand == groups[0].guard


def test_probability_choice_stays_in_one_transition_group() -> None:
    graph = cfg("x := 0; if prob(0.4) then x := 1; else x := 2; fi;")
    choice = location_of_kind(graph, "probabilistic")
    groups = graph.outgoing(choice.id)
    assert len(groups) == 1
    assert len(groups[0].branches) == 2
    assert format_expr(groups[0].branches[0].probability) == "0.4"
    assert format_expr(groups[0].branches[1].probability) == "1 - 0.4"


def test_symbolic_probability_creates_a_range_obligation() -> None:
    graph = cfg("p := 0.5; if prob(p) then skip; else skip; fi;")
    report = validate_cfg(graph)
    assert len(report.probability_obligations) == 1
    assert "prove 0 <= p <= 1" in report.probability_obligations[0]


def test_while_body_returns_to_header_and_annotation_is_attached() -> None:
    graph = cfg("x := 0; {x >= 0} while x < 2 do {x < 2} x := x + 1; od;")
    loop = location_of_kind(graph, "while")
    body = next(
        branch.destination
        for group in graph.outgoing(loop.id)
        if format_expr(group.guard) == "x < 2"
        for branch in group.branches
    )
    assert graph.outgoing(body)[0].branches[0].destination == loop.id
    assert format_expr(loop.invariant) == "x >= 0"
    assert format_expr(graph.locations[body].invariant) == "x < 2"


def test_assert_and_refute_edges_and_absorbing_terminals() -> None:
    asserted = cfg("x := 0; assert x = 0;")
    assertion = location_of_kind(asserted, "assert")
    edges = {
        format_expr(group.guard): group.branches[0].destination
        for group in asserted.outgoing(assertion.id)
    }
    assert edges["x = 0"] == asserted.normal_terminal
    assert edges["not x = 0"] == asserted.failure_terminal

    refuted = cfg("x := 0; refute x = 0;")
    refute = location_of_kind(refuted, "refute")
    edges = {
        format_expr(group.guard): group.branches[0].destination
        for group in refuted.outgoing(refute.id)
    }
    assert edges["x = 0"] == refuted.failure_terminal
    for terminal in (refuted.normal_terminal, refuted.failure_terminal):
        assert refuted.outgoing(terminal)[0].branches[0].destination == terminal


def test_distribution_assignment_records_fresh_sample_and_update() -> None:
    graph = cfg("r := Uniform(0, 2); x := 1; x := r * x;")
    sample_location = location_of_kind(graph, "sample")
    update = graph.outgoing(sample_location.id)[0].branches[0].update
    assert len(update.samples) == 1
    assert update.samples[0].fresh is True
    assert update.samples[0].distribution.name == "Uniform"
    assert isinstance(update.assignments["r"], Variable)
    assert update.assignments["r"].name.startswith("__sample_r_")


def test_declared_random_is_sampled_on_each_using_transition() -> None:
    graph = cfg("random z ~ Bernoulli(0.5); x := 0; x := x + z;")
    updates = {
        format_expr(branch.update.assignments["x"]): branch.update
        for group in graph.transitions
        for branch in group.branches
        if "x" in branch.update.assignments
    }
    assert len(updates["0"].samples) == 0
    assert [sample.symbol for sample in updates["x + z"].samples] == ["z"]


def test_cfg_generation_is_stable_and_json_has_grouped_schema() -> None:
    source = "x := 0; while x < 1 do x := x + 1; od; refute x > 2;"
    first, second = cfg(source), cfg(source)
    assert cfg_to_data(first) == cfg_to_data(second)
    data = cfg_to_data(first)
    assert data["schema_version"] == 1
    assert "transition_groups" in data
    assert data["failure_terminal"] == "l_f"
