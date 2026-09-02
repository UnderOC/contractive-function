from __future__ import annotations

from collections import defaultdict

from contractive_tool.frontend.ast import (
    Annotation,
    Assert,
    Assign,
    Assume,
    Binary,
    BooleanConstant,
    BoolBinary,
    DistributionExpr,
    Expr,
    If,
    Number,
    ProbChoice,
    Refute,
    Sequence,
    Skip,
    SourceSpan,
    Variable,
    While,
    negate,
)
from contractive_tool.ir.cfg import (
    Branch,
    Location,
    ProgramCFG,
    RandomSample,
    TransitionGroup,
    Update,
)
from contractive_tool.ir.program import ProgramIR


class _Builder:
    def __init__(self, program: ProgramIR):
        self.program = program
        self.locations: dict[str, Location] = {}
        self.transitions: list[TransitionGroup] = []
        self.location_counts: defaultdict[str, int] = defaultdict(int)
        self.transition_count = 0
        self.sample_count = 0
        self.true = BooleanConstant(True, SourceSpan.synthetic(program.ast.source_file))
        self.one = Number("1", SourceSpan.synthetic(program.ast.source_file))
        self.normal_terminal = self._location("terminal", None, explicit_id="l_t")
        self.failure_terminal: str | None = None
        self._transition(
            self.normal_terminal,
            self.true,
            (Branch(self.normal_terminal, self.one, Update({})),),
            None,
            explicit_id="T_absorb_normal",
        )

    def _location(
        self,
        kind: str,
        span: SourceSpan | None,
        *,
        explicit_id: str | None = None,
        invariant: Expr | None = None,
    ) -> str:
        if explicit_id is None:
            self.location_counts[kind] += 1
            location_id = f"L_{kind}_{self.location_counts[kind]}"
        else:
            location_id = explicit_id
        self.locations[location_id] = Location(location_id, kind, span, invariant or self.true)
        return location_id

    def _transition(
        self,
        source: str,
        guard: Expr,
        branches: tuple[Branch, ...],
        origin: SourceSpan | None,
        *,
        explicit_id: str | None = None,
    ) -> None:
        if explicit_id is None:
            self.transition_count += 1
            transition_id = f"T_{self.transition_count}"
        else:
            transition_id = explicit_id
        self.transitions.append(TransitionGroup(transition_id, source, guard, branches, origin))

    def _ensure_failure(self) -> str:
        if self.failure_terminal is None:
            self.failure_terminal = self._location("terminal", None, explicit_id="l_f")
            self._transition(
                self.failure_terminal,
                self.true,
                (Branch(self.failure_terminal, self.one, Update({})),),
                None,
                explicit_id="T_absorb_failure",
            )
        return self.failure_terminal

    def _attach_invariant(self, location_id: str, predicate: Expr) -> None:
        location = self.locations[location_id]
        if isinstance(location.invariant, BooleanConstant) and location.invariant.value:
            invariant = predicate
        else:
            invariant = BoolBinary("and", predicate, location.invariant, predicate.span)
        self.locations[location_id] = Location(
            location.id, location.kind, location.span, invariant
        )

    def _random_names(self, expr: Expr) -> set[str]:
        result: set[str] = set()

        def visit(item: Expr) -> None:
            if isinstance(item, Variable) and item.name in self.program.random_distributions:
                result.add(item.name)
            elif hasattr(item, "operand"):
                visit(item.operand)
            elif isinstance(item, (Binary, BoolBinary)):
                visit(item.left)
                visit(item.right)
            elif hasattr(item, "left") and hasattr(item, "right"):
                visit(item.left)
                visit(item.right)

        visit(expr)
        return result

    def _assignment_update(self, stmt: Assign) -> Update:
        if isinstance(stmt.value, DistributionExpr):
            self.sample_count += 1
            symbol = f"__sample_{stmt.target}_{self.sample_count}"
            sample = RandomSample(symbol, stmt.value)
            return Update({stmt.target: Variable(symbol, stmt.value.span)}, (sample,))
        samples = tuple(
            RandomSample(name, self.program.random_distributions[name])
            for name in sorted(self._random_names(stmt.value))
        )
        return Update({stmt.target: stmt.value}, samples)

    def build_sequence(self, sequence: Sequence, continuation: str) -> str:
        entry = continuation
        for stmt in reversed(sequence.statements):
            if isinstance(stmt, Annotation):
                self._attach_invariant(entry, stmt.predicate)
            else:
                entry = self.build_statement(stmt, entry)
        return entry

    def build_statement(self, stmt, continuation: str) -> str:
        if isinstance(stmt, Assign):
            entry = self._location(
                "sample" if isinstance(stmt.value, DistributionExpr) else "assign", stmt.span
            )
            branch = Branch(continuation, self.one, self._assignment_update(stmt))
            self._transition(entry, self.true, (branch,), stmt.span)
            return entry
        if isinstance(stmt, Skip):
            entry = self._location("skip", stmt.span)
            self._transition(
                entry, self.true, (Branch(continuation, self.one, Update({})),), stmt.span
            )
            return entry
        if isinstance(stmt, Assume):
            entry = self._location("assume", stmt.span)
            self._transition(
                entry, stmt.condition, (Branch(continuation, self.one, Update({})),), stmt.span
            )
            return entry
        if isinstance(stmt, If):
            then_entry = self.build_sequence(stmt.then_branch, continuation)
            else_entry = self.build_sequence(stmt.else_branch, continuation)
            if isinstance(stmt.condition, ProbChoice):
                entry = self._location("probabilistic", stmt.span)
                probability = stmt.condition.probability
                complement = Binary("-", self.one, probability, probability.span)
                branches = (
                    Branch(then_entry, probability, Update({})),
                    Branch(else_entry, complement, Update({})),
                )
                self._transition(entry, self.true, branches, stmt.span)
            else:
                entry = self._location("branch", stmt.span)
                self._transition(
                    entry,
                    stmt.condition,
                    (Branch(then_entry, self.one, Update({})),),
                    stmt.span,
                )
                self._transition(
                    entry,
                    negate(stmt.condition),
                    (Branch(else_entry, self.one, Update({})),),
                    stmt.span,
                )
            return entry
        if isinstance(stmt, While):
            entry = self._location("while", stmt.span, invariant=stmt.invariant)
            body_entry = self.build_sequence(stmt.body, entry)
            self._transition(
                entry,
                stmt.guard,
                (Branch(body_entry, self.one, Update({})),),
                stmt.span,
            )
            self._transition(
                entry,
                negate(stmt.guard),
                (Branch(continuation, self.one, Update({})),),
                stmt.span,
            )
            return entry
        if isinstance(stmt, (Assert, Refute)):
            failure = self._ensure_failure()
            kind = "assert" if isinstance(stmt, Assert) else "refute"
            entry = self._location(kind, stmt.span)
            failure_guard = negate(stmt.condition) if isinstance(stmt, Assert) else stmt.condition
            success_guard = stmt.condition if isinstance(stmt, Assert) else negate(stmt.condition)
            self._transition(
                entry,
                success_guard,
                (Branch(continuation, self.one, Update({})),),
                stmt.span,
            )
            self._transition(
                entry,
                failure_guard,
                (Branch(failure, self.one, Update({})),),
                stmt.span,
            )
            return entry
        raise TypeError(f"unsupported statement: {type(stmt).__name__}")

    def finish(self) -> ProgramCFG:
        initial = self.build_sequence(self.program.ast.body, self.normal_terminal)
        return ProgramCFG(
            locations=dict(self.locations),
            transitions=tuple(self.transitions),
            symbols=self.program.symbols,
            initial_location=initial,
            normal_terminal=self.normal_terminal,
            failure_terminal=self.failure_terminal,
            source_file=self.program.ast.source_file,
        )


def build_cfg(program: ProgramIR) -> ProgramCFG:
    """Build a grouped pCFG using continuation-passing construction."""
    return _Builder(program).finish()

