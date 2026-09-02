from __future__ import annotations

import pytest

from contractive_tool.errors import SemanticError
from contractive_tool.frontend.parser import parse_text
from contractive_tool.frontend.semantic import check_program


def check(source: str):
    return check_program(parse_text(source, "semantic.pp"))


def test_symbols_are_bound_from_assignments() -> None:
    program = check("x := 1; y := x + 2;")
    assert program.symbols.program_variables == ("x", "y")
    assert program.symbols.declared_random_variables == ()


def test_explicit_random_declaration_is_fresh_source() -> None:
    program = check("random noise ~ Normal(0, 1); x := 0; x := x + noise;")
    assert program.symbols.declared_random_variables == ("noise",)
    assert program.random_distributions["noise"].name == "Normal"


@pytest.mark.parametrize(
    "source, message",
    [
        ("x := missing + 1;", "unknown variable 'missing'"),
        ("x := 0; if not prob(0.5) then skip; else skip; fi;", "only valid as the direct"),
        ("x := 0; if prob(1.5) then skip; else skip; fi;", "probability must be in [0, 1]"),
        ("x := Unif(2, 1);", "lower bound < upper bound"),
        ("x := Normal(0, 0);", "positive standard deviation"),
        ("random r ~ Uniform(0, 1); r := 2;", "cannot assign to declared random"),
    ],
)
def test_semantic_errors_are_actionable(source: str, message: str) -> None:
    with pytest.raises(SemanticError) as error:
        check(source)
    assert message in str(error.value)
    assert "semantic.pp:1:" in str(error.value)


def test_distribution_alias_and_constants_are_normalized() -> None:
    program = check("r := Unif(0 + 0, 1 * 2);")
    assignment = program.ast.body.statements[0]
    assert assignment.value.name == "Uniform"
    assert [arg.text for arg in assignment.value.arguments] == ["0", "2"]

