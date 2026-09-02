from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from lark import Lark, Token, Transformer, UnexpectedInput, v_args

from contractive_tool.errors import Diagnostic, ParseError
from contractive_tool.frontend.ast import (
    Annotation,
    Assert,
    Assign,
    Assume,
    Binary,
    BooleanConstant,
    BoolBinary,
    BoolUnary,
    Compare,
    DistributionExpr,
    If,
    Number,
    ProbChoice,
    Program,
    RandomDeclaration,
    Refute,
    Sequence,
    Skip,
    SourceSpan,
    Unary,
    Variable,
    While,
)


def _span(meta: object, source_file: str) -> SourceSpan:
    return SourceSpan(
        source_file,
        meta.line,
        meta.column,
        meta.end_line,
        meta.end_column,
    )


@v_args(meta=True)
class _ASTBuilder(Transformer):
    def __init__(self, source_file: str):
        super().__init__()
        self.source_file = source_file

    def start(self, meta, children):
        return children[0]

    def program(self, meta, children):
        declarations = tuple(item for item in children if isinstance(item, RandomDeclaration))
        body = next(item for item in children if isinstance(item, Sequence))
        return Program(declarations, body, self.source_file)

    def block(self, meta, children):
        return Sequence(tuple(children), _span(meta, self.source_file))

    def random_decl(self, meta, children):
        return RandomDeclaration(str(children[0]), children[1], _span(meta, self.source_file))

    def skip_stmt(self, meta, children):
        return Skip(_span(meta, self.source_file))

    def assign_stmt(self, meta, children):
        return Assign(str(children[0]), children[1], _span(meta, self.source_file))

    def assert_stmt(self, meta, children):
        return Assert(children[0], _span(meta, self.source_file))

    def refute_stmt(self, meta, children):
        return Refute(children[0], _span(meta, self.source_file))

    def assume_stmt(self, meta, children):
        return Assume(children[0], _span(meta, self.source_file))

    def annotation(self, meta, children):
        return Annotation(children[0], _span(meta, self.source_file))

    def if_stmt(self, meta, children):
        return If(children[0], children[1], children[2], _span(meta, self.source_file))

    def while_stmt(self, meta, children):
        if len(children) == 3:
            guard, invariant, body = children
        else:
            guard, body = children
            invariant = None
        return While(guard, invariant, body, _span(meta, self.source_file))

    def distribution(self, meta, children):
        return DistributionExpr(
            str(children[0]), tuple(children[1:]), _span(meta, self.source_file)
        )

    def true_expr(self, meta, children):
        return BooleanConstant(True, _span(meta, self.source_file))

    def false_expr(self, meta, children):
        return BooleanConstant(False, _span(meta, self.source_file))

    def prob_expr(self, meta, children):
        return ProbChoice(children[0], _span(meta, self.source_file))

    def compare_expr(self, meta, children):
        return Compare(str(children[1]), children[0], children[2], _span(meta, self.source_file))

    def not_expr(self, meta, children):
        return BoolUnary("not", children[-1], _span(meta, self.source_file))

    def disjunction(self, meta, children):
        operands = children[::2]
        result = operands[0]
        for operand in operands[1:]:
            result = BoolBinary("or", result, operand, _span(meta, self.source_file))
        return result

    def conjunction(self, meta, children):
        operands = children[::2]
        result = operands[0]
        for operand in operands[1:]:
            result = BoolBinary("and", result, operand, _span(meta, self.source_file))
        return result

    def number_expr(self, meta, children):
        return Number(str(children[0]), _span(meta, self.source_file))

    def variable_expr(self, meta, children):
        return Variable(str(children[0]), _span(meta, self.source_file))

    def neg_expr(self, meta, children):
        return Unary("-", children[-1], _span(meta, self.source_file))

    def pos_expr(self, meta, children):
        return Unary("+", children[-1], _span(meta, self.source_file))

    def sum(self, meta, children):
        result = children[0]
        for index in range(1, len(children), 2):
            result = Binary(
                str(children[index]), result, children[index + 1], _span(meta, self.source_file)
            )
        return result

    def product(self, meta, children):
        result = children[0]
        for index in range(1, len(children), 2):
            result = Binary("*", result, children[index + 1], _span(meta, self.source_file))
        return result


_GRAMMAR = files("contractive_tool.frontend").joinpath("grammar.lark").read_text(encoding="utf-8")
_PARSER = Lark(_GRAMMAR, parser="lalr", propagate_positions=True, maybe_placeholders=False)


def parse_text(text: str, source_file: str = "<input>") -> Program:
    try:
        tree = _PARSER.parse(text)
        return _ASTBuilder(source_file).transform(tree)
    except UnexpectedInput as error:
        expected = ", ".join(sorted(error.expected)) if getattr(error, "expected", None) else "valid syntax"
        diagnostic = Diagnostic(
            f"syntax error; expected {expected}", source_file, error.line, error.column
        )
        raise ParseError([diagnostic]) from error


def parse_file(path: str | Path) -> Program:
    source_path = Path(path)
    return parse_text(source_path.read_text(encoding="utf-8"), str(source_path.resolve()))

