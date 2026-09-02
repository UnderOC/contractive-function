from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import sympy as sp

from contractive_tool.analysis_pipeline import AnalysisRequest, generate_analysis
from contractive_tool.errors import AnalysisError, FrontendError
from contractive_tool.frontend.ast import ast_to_data
from contractive_tool.frontend.parser import parse_file
from contractive_tool.frontend.semantic import check_program
from contractive_tool.pipeline import compile_to_cfg


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="contractive",
        description="Parse .pp programs and generate a validated grouped probabilistic CFG.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    parse = subcommands.add_parser("parse", help="parse and semantically check a .pp source")
    parse.add_argument("source", type=Path)
    parse.add_argument("--out", type=Path, required=True, help="AST JSON output file")

    cfg = subcommands.add_parser("cfg", help="run the complete frontend and emit pCFG artifacts")
    cfg.add_argument("source", type=Path)
    cfg.add_argument("--out-dir", type=Path, help="artifact directory")

    analyze = subcommands.add_parser(
        "analyze", help="generate stage 2/3 goal, template and obligation artifacts"
    )
    analyze.add_argument("source", type=Path)
    analyze.add_argument("--out-dir", type=Path, required=True)
    analyze.add_argument("--analysis-id", default="main")
    analyze.add_argument(
        "--goal", required=True, choices=("tail_bound", "assertion_violation")
    )
    analyze.add_argument(
        "--certificate",
        required=True,
        choices=("kelly", "polynomial-eta", "direct-theta", "factorized"),
    )
    analyze.add_argument("--event")
    analyze.add_argument("--event-mode", default="at_horizon", choices=("at_horizon", "by_horizon"))
    analyze.add_argument("--horizon", type=int)
    analyze.add_argument("--initial", action="append", default=[], metavar="NAME=VALUE")
    analyze.add_argument("--initial-location")
    analyze.add_argument("--degree", type=int, default=1)
    analyze.add_argument("--rho", help="fixed contraction factor; Kelly defaults to its exact moment")
    analyze.add_argument("--normalization-scale", default="1")
    analyze.add_argument("--positivity-margin", default="0")
    analyze.add_argument("--base")
    analyze.add_argument("--lambda", dest="lambda_value")
    analyze.add_argument("--threshold")
    analyze.add_argument("--factor-q")
    analyze.add_argument("--k", type=int, default=1)
    return parser


def _exact(text: str) -> sp.Expr:
    try:
        return sp.sympify(text, rational=True)
    except (sp.SympifyError, TypeError) as error:
        raise AnalysisError(f"invalid exact numeric expression: {text!r}") from error


def _initial_values(items: list[str]) -> dict[str, sp.Expr]:
    result: dict[str, sp.Expr] = {}
    for item in items:
        if "=" not in item:
            raise AnalysisError(f"--initial expects NAME=VALUE, got {item!r}")
        name, text = item.split("=", 1)
        if not name or name in result:
            raise AnalysisError(f"invalid or duplicate initial variable {name!r}")
        value = _exact(text)
        if value.free_symbols:
            raise AnalysisError("initial values must be fixed numeric expressions")
        result[name] = value
    return result


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "parse":
            checked = check_program(parse_file(args.source))
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(
                json.dumps(ast_to_data(checked.ast), indent=2, sort_keys=True, ensure_ascii=False)
                + "\n",
                encoding="utf-8",
            )
            print(json.dumps({"status": "ok", "ast": str(args.out.resolve())}))
            return 0

        if args.command == "cfg":
            out_dir = args.out_dir or Path("generated") / args.source.stem
            summary = compile_to_cfg(args.source, out_dir)
        else:
            request = AnalysisRequest(
                goal=args.goal,
                certificate=args.certificate,
                analysis_id=args.analysis_id,
                initial=_initial_values(args.initial),
                initial_location=args.initial_location,
                event=args.event,
                horizon=args.horizon,
                event_mode=args.event_mode,
                degree=args.degree,
                rho=_exact(args.rho) if args.rho else None,
                normalization_scale=_exact(args.normalization_scale),
                positivity_margin=_exact(args.positivity_margin),
                base_variable=args.base,
                lambda_value=_exact(args.lambda_value) if args.lambda_value else None,
                threshold=_exact(args.threshold) if args.threshold else None,
                factor_q=_exact(args.factor_q) if args.factor_q else None,
                k=args.k,
            )
            summary = generate_analysis(args.source, args.out_dir, request)
        print(json.dumps({"status": "ok", **summary}, sort_keys=True))
        return 0
    except (AnalysisError, FrontendError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
