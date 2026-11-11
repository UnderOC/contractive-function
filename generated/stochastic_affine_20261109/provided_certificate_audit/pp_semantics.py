#!/usr/bin/env python3
"""Small, exact reader for the .pp subset used by this benchmark package.

It is an independent source/annotation sanity checker, not the user's frontend
and not a replacement for the mathematical proofs in the family READMEs.
All finite decimal constants are interpreted as rational numbers, not floats.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from fractions import Fraction as F
from pathlib import Path


def evaluate(text, env):
    source = re.sub(r"(?<![<>=!])=(?!=)", "==", text).replace("^", "**")
    tree = ast.parse(source.strip(), mode="eval")

    def ev(node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                return node.value
            return F(ast.get_source_segment(source.strip(), node))
        if isinstance(node, ast.Name):
            if node.id in ("true", "True"):
                return True
            if node.id in ("false", "False"):
                return False
            return env[node.id]
        if isinstance(node, ast.UnaryOp):
            x = ev(node.operand)
            if isinstance(node.op, ast.USub):
                return -x
            if isinstance(node.op, ast.UAdd):
                return x
            if isinstance(node.op, ast.Not):
                return not x
        if isinstance(node, ast.BinOp):
            x, y = ev(node.left), ev(node.right)
            if isinstance(node.op, ast.Add):
                return x + y
            if isinstance(node.op, ast.Sub):
                return x - y
            if isinstance(node.op, ast.Mult):
                return x * y
            if isinstance(node.op, ast.Div):
                return x / y
            if isinstance(node.op, ast.Pow) and getattr(y, "denominator", 1) == 1:
                return x ** int(y)
        if isinstance(node, ast.BoolOp):
            return all(ev(v) for v in node.values) if isinstance(node.op, ast.And) else any(ev(v) for v in node.values)
        if isinstance(node, ast.Compare):
            x = ev(node.left)
            for op, right in zip(node.ops, node.comparators):
                y = ev(right)
                if isinstance(op, ast.Lt):
                    ok = x < y
                elif isinstance(op, ast.LtE):
                    ok = x <= y
                elif isinstance(op, ast.Gt):
                    ok = x > y
                elif isinstance(op, ast.GtE):
                    ok = x >= y
                elif isinstance(op, ast.Eq):
                    ok = x == y
                elif isinstance(op, ast.NotEq):
                    ok = x != y
                else:
                    raise ValueError(type(op).__name__)
                if not ok:
                    return False
                x = y
            return True
        raise ValueError(f"Unsupported expression: {ast.dump(node)}")

    return ev(tree.body)


@dataclass
class Statement:
    kind: str
    expression: str = ""
    target: str = ""
    left: tuple = ()
    right: tuple = ()


class Parser:
    def __init__(self, text):
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
        text = re.sub(r"//[^\n]*", "", text)
        pattern = r"\s+|(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?|[A-Za-z_]\w*|:=|>=|<=|!=|==|\*\*|[{}();+*/^<>=-]"
        self.tokens = []
        end = 0
        for m in re.finditer(pattern, text):
            if m.start() != end:
                raise SyntaxError(f"Unrecognized source near {text[end:end+40]!r}")
            if not m.group().isspace():
                self.tokens.append(m.group())
            end = m.end()
        if end != len(text):
            raise SyntaxError(text[end:])
        self.i = 0

    def peek(self):
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def take(self, expected=None):
        x = self.peek()
        if expected is not None and x != expected:
            raise SyntaxError(f"Expected {expected}, received {x}")
        self.i += 1
        return x

    def until(self, stops):
        result = []
        depth = 0
        while self.peek() is not None:
            x = self.peek()
            if depth == 0 and x in stops:
                break
            x = self.take()
            depth += (x == "(") - (x == ")")
            result.append(x)
        if not result:
            raise SyntaxError("Empty expression")
        return " ".join(result)

    def sequence(self, stops=()):
        result = []
        while self.peek() is not None and self.peek() not in stops:
            token = self.take()
            if token == ";":
                continue
            if token == "{":
                result.append(Statement("annotation", self.until({"}"})))
                self.take("}")
            elif token == "while":
                guard = self.until({"do"})
                self.take("do")
                body = self.sequence({"od"})
                self.take("od")
                result.append(Statement("while", guard, left=body))
            elif token == "if":
                guard = self.until({"then"})
                self.take("then")
                yes = self.sequence({"else", "fi"})
                no = ()
                if self.peek() == "else":
                    self.take("else")
                    no = self.sequence({"fi"})
                self.take("fi")
                if guard.startswith("prob "):
                    guard = guard[len("prob "):].strip()
                    result.append(Statement("prob", guard, left=yes, right=no))
                else:
                    result.append(Statement("if", guard, left=yes, right=no))
            elif token == "refute":
                result.append(Statement("refute", self.until({";"})))
            elif re.fullmatch(r"[A-Za-z_]\w*", token):
                self.take(":=")
                expression = self.until({";", "{", "if", "while", "else", "fi", "od", "refute"})
                result.append(Statement("assign", expression, token))
            else:
                raise SyntaxError(f"Unexpected token {token}")
        return tuple(result)


def execute(statements, state, check_annotations=True):
    distribution = [(F(1), dict(state))]
    for statement in statements:
        output = []
        for probability, env in distribution:
            k = statement.kind
            if k == "annotation":
                if check_annotations and not evaluate(statement.expression, env):
                    raise AssertionError(f"Annotation failed: {{{statement.expression}}}; state={env}")
                output.append((probability, env))
            elif k == "assign":
                nxt = dict(env)
                nxt[statement.target] = evaluate(statement.expression, env)
                output.append((probability, nxt))
            elif k in ("if", "prob"):
                if k == "if":
                    choices = [(F(1), statement.left if evaluate(statement.expression, env) else statement.right)]
                else:
                    p = evaluate(statement.expression, env)
                    assert 0 <= p <= 1
                    choices = [(p, statement.left), (1-p, statement.right)]
                for weight, body in choices:
                    if weight:
                        output.extend((probability * weight * p, e) for p, e in execute(body, env, check_annotations))
            elif k == "refute":
                output.append((probability, env))
            else:
                raise ValueError("Nested loops are not part of this benchmark checker")
        distribution = output
    return distribution


class Program:
    def __init__(self, path):
        self.path = Path(path)
        self.statements = Parser(self.path.read_text()).sequence()
        indices = [i for i, s in enumerate(self.statements) if s.kind == "while"]
        assert len(indices) == 1, "Expected exactly one top-level loop"
        i = indices[0]
        self.prefix, self.loop, self.suffix = self.statements[:i], self.statements[i], self.statements[i+1:]
        self.invariants = []
        for s in reversed(self.prefix):
            if s.kind != "annotation":
                break
            self.invariants.append(s.expression)
        init = execute(self.prefix, {})
        assert len(init) == 1 and init[0][0] == 1
        self.initial = init[0][1]

    def active(self, state):
        return evaluate(self.loop.expression, state)

    def check_invariant(self, state):
        for expr in self.invariants:
            assert evaluate(expr, state), f"{self.path.name}: invariant {expr} at {state}"

    def successors(self, state):
        assert self.active(state)
        self.check_invariant(state)
        distribution = execute(self.loop.left, state)
        assert sum(p for p, _ in distribution) == 1
        for _, nxt in distribution:
            self.check_invariant(nxt)
            if not self.active(nxt):
                execute(self.suffix, nxt)
        return distribution

    def check_prefix_tree(self, depth=4):
        """Finite exact checks detect coding mistakes; they are not a universal proof."""
        frontier = {tuple(sorted(self.initial.items()))}
        transitions = 0
        for _ in range(depth):
            new = set()
            for frozen in frontier:
                state = dict(frozen)
                self.check_invariant(state)
                if self.active(state):
                    for _, nxt in self.successors(state):
                        transitions += 1
                        new.add(tuple(sorted(nxt.items())))
                else:
                    execute(self.suffix, state)
            frontier = new
        return {"file": self.path.name, "depth": depth, "branch_transitions_checked": transitions}


if __name__ == "__main__":
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--depth", type=int, default=4)
    args = parser.parse_args()
    for path in args.paths:
        print(json.dumps(Program(path).check_prefix_tree(args.depth)))
