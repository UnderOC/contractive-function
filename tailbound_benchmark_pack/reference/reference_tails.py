#!/usr/bin/env python3
"""Exact P(C > n) for selected normalized loop-iteration benchmarks.

Python 3.10+, standard library only. No simulation and no baseline solver.
Integer-weight dynamic programming returns exact fractions. The decimal column
is a display approximation. These are NOT original-paper CFG-step runtimes.
"""
from __future__ import annotations

import argparse
import csv
import sys
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path
from typing import Iterator


def require_nonnegative_int(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")


def coupon_tails(coupons: int, max_n: int) -> Iterator[tuple[int, Fraction]]:
    """Uniform coupon collection from an empty collection; C counts draws.

    State k records how many distinct coupons have been collected. Each path
    count has k continuations with an old coupon and N-k with a new coupon.
    Completed collections are discarded: their probability is no longer tail
    mass. At horizon n the common denominator is N**n.
    """
    require_nonnegative_int(coupons, "coupons")
    require_nonnegative_int(max_n, "max_n")
    if coupons == 0:
        raise ValueError("coupons must be positive")
    ways = [1] + [0] * (coupons - 1)
    denominator = 1
    yield 0, Fraction(1)
    for n in range(1, max_n + 1):
        nxt = [0] * coupons
        for k, count in enumerate(ways):
            nxt[k] += count * k
            if k + 1 < coupons:
                nxt[k + 1] += count * (coupons - k)
        ways = nxt
        denominator *= coupons
        yield n, Fraction(sum(ways), denominator)


def walk_tails(start: int, down_prob: Fraction, max_n: int) -> Iterator[tuple[int, Fraction]]:
    """Nearest-neighbor walk absorbed at zero; C counts updates.

    Positive states remaining after n updates contribute exactly P(C > n).
    A fraction a/b is implemented by integer path weights a and b-a, with
    common denominator b**n. This is O(max_n**2) state transitions in general.
    """
    require_nonnegative_int(start, "start")
    require_nonnegative_int(max_n, "max_n")
    if not isinstance(down_prob, Fraction):
        raise TypeError("down_prob must be fractions.Fraction, not a float")
    if not 0 <= down_prob <= 1:
        raise ValueError("down_prob must lie in [0, 1]")
    a, b = down_prob.numerator, down_prob.denominator
    weights = {start: 1} if start else {}
    denominator = 1
    yield 0, Fraction(bool(start))
    for n in range(1, max_n + 1):
        nxt: dict[int, int] = {}
        for x, count in weights.items():
            if x > 1 and a:
                nxt[x - 1] = nxt.get(x - 1, 0) + a * count
            if b != a:
                nxt[x + 1] = nxt.get(x + 1, 0) + (b - a) * count
        weights = nxt
        denominator *= b
        yield n, Fraction(sum(weights.values()), denominator)


def polynomial_tails(max_n: int) -> Iterator[tuple[int, Fraction]]:
    """Appendix G: P(C >= d)=1/(d+1)**2, so P(C > n)=1/(n+2)**2.

    The loop may execute zero times; in particular P(C > 0)=1/4, not 1.
    """
    require_nonnegative_int(max_n, "max_n")
    for n in range(max_n + 1):
        yield n, Fraction(1, (n + 2) ** 2)


def as_decimal(value: Fraction) -> str:
    with localcontext() as context:
        context.prec = 45
        return format(Decimal(value.numerator) / Decimal(value.denominator), ".36E")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("family", choices=("all", "coupon", "walk", "poly"))
    parser.add_argument("--max-n", type=int, default=200)
    parser.add_argument("--coupons", type=int, default=2)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--down-prob", default="0.6", help="Exact decimal or fraction, e.g. 0.6 or 3/5")
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        require_nonnegative_int(args.max_n, "max_n")
        require_nonnegative_int(args.coupons, "coupons")
        require_nonnegative_int(args.start, "start")
        if not args.coupons:
            raise ValueError("coupons must be positive")
        p = Fraction(args.down_prob)
        if not 0 <= p <= 1:
            raise ValueError("down-prob must lie in [0, 1]")
        jobs: list[tuple[str, Iterator[tuple[int, Fraction]]]] = []
        if args.family == "all":
            jobs = [
                ("01_coupon2", coupon_tails(2, args.max_n)),
                ("02_coupon4", coupon_tails(4, args.max_n)),
                ("03_rw_int", walk_tails(1, Fraction(3, 5), args.max_n)),
                ("07_polynomial_tail", polynomial_tails(args.max_n)),
            ]
        elif args.family == "coupon":
            jobs = [(f"coupon_N{args.coupons}", coupon_tails(args.coupons, args.max_n))]
        elif args.family == "walk":
            jobs = [(f"walk_x{args.start}_p{p.numerator}over{p.denominator}", walk_tails(args.start, p, args.max_n))]
        else:
            jobs = [("07_polynomial_tail", polynomial_tails(args.max_n))]
        args.output.parent.mkdir(parents=True, exist_ok=True)
        count = 0
        with args.output.open("w", encoding="utf-8", newline="") as out:
            writer = csv.writer(out)
            writer.writerow(["benchmark", "clock", "event", "horizon_n", "exact_numerator", "exact_denominator", "decimal_approx"])
            for name, values in jobs:
                previous = Fraction(1)
                for n, q in values:
                    if not 0 <= q <= previous:
                        raise ArithmeticError(f"Invalid tail sequence: {name}, n={n}, q={q}")
                    previous = q
                    writer.writerow([name, "loop_body_executions", "Pr(C > n)", n, q.numerator, q.denominator, as_decimal(q)])
                    count += 1
        print(f"Wrote {count} exact tail values to {args.output}")
        return 0
    except (ValueError, TypeError, OSError, ArithmeticError) as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    sys.exit(main())
