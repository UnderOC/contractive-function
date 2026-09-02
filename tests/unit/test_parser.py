from __future__ import annotations

import pytest

from contractive_tool.errors import ParseError
from contractive_tool.frontend.ast import (
    Annotation,
    Assign,
    Binary,
    BoolBinary,
    If,
    ProbChoice,
    Refute,
    While,
)
from contractive_tool.frontend.parser import parse_text


def test_arithmetic_and_boolean_precedence() -> None:
    program = parse_text(
        "{x + 2 * y <= 7 or x = 0 and not y < 1} x := x - y * 3;",
        "precedence.pp",
    )
    annotation, assignment = program.body.statements
    assert isinstance(annotation, Annotation)
    assert isinstance(annotation.predicate, BoolBinary)
    assert annotation.predicate.operator == "or"
    assert isinstance(annotation.predicate.right, BoolBinary)
    assert annotation.predicate.right.operator == "and"
    assert isinstance(assignment, Assign)
    assert isinstance(assignment.value, Binary)
    assert assignment.value.operator == "-"
    assert isinstance(assignment.value.right, Binary)
    assert assignment.value.right.operator == "*"


def test_control_statements_probability_and_optional_semicolons() -> None:
    program = parse_text(
        """
        x := 0
        while x < 3 invariant x >= 0 do
          if prob(0.25) then x := x + 1 else skip fi;
        od
        refute (x >= 3)
        """,
        "control.pp",
    )
    assignment, loop, refute = program.body.statements
    assert isinstance(assignment, Assign)
    assert isinstance(loop, While)
    assert loop.invariant is not None
    conditional = loop.body.statements[0]
    assert isinstance(conditional, If)
    assert isinstance(conditional.condition, ProbChoice)
    assert isinstance(refute, Refute)


def test_source_spans_are_preserved() -> None:
    program = parse_text("\n\nvalue := 4;", "span.pp")
    assignment = program.body.statements[0]
    assert assignment.span.file == "span.pp"
    assert assignment.span.start_line == 3
    assert assignment.span.start_column == 1


def test_comments_and_unicode_operators() -> None:
    program = parse_text("/* a */ {x ≤ 2 ∧ ¬ x < 0} // b\nx := x + 1;", "unicode.pp")
    assert len(program.body.statements) == 2


def test_parse_error_reports_actual_location() -> None:
    with pytest.raises(ParseError) as error:
        parse_text("x := ;", "broken.pp")
    assert error.value.diagnostics[0].file == "broken.pp"
    assert error.value.diagnostics[0].line == 1

