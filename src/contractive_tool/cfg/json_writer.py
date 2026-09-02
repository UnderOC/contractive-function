from __future__ import annotations

from contractive_tool.frontend.ast import ast_to_data
from contractive_tool.ir.cfg import ProgramCFG


def cfg_to_data(cfg: ProgramCFG) -> dict[str, object]:
    locations = []
    for location in cfg.locations.values():
        locations.append(
            {
                "id": location.id,
                "kind": location.kind,
                "span": ast_to_data(location.span),
                "invariant": ast_to_data(location.invariant),
            }
        )

    transitions = []
    for group in cfg.transitions:
        branches = []
        for branch in group.branches:
            branches.append(
                {
                    "destination": branch.destination,
                    "probability": ast_to_data(branch.probability),
                    "update": {
                        "semantics": "simultaneous",
                        "assignments": {
                            name: ast_to_data(expression)
                            for name, expression in sorted(branch.update.assignments.items())
                        },
                        "samples": [ast_to_data(sample) for sample in branch.update.samples],
                    },
                }
            )
        transitions.append(
            {
                "id": group.id,
                "source": group.source,
                "guard": ast_to_data(group.guard),
                "branches": branches,
                "origin": ast_to_data(group.origin),
            }
        )

    return {
        "schema_version": 1,
        "source_file": cfg.source_file,
        "symbols": {
            "program_variables": list(cfg.symbols.program_variables),
            "declared_random_variables": list(cfg.symbols.declared_random_variables),
        },
        "initial_location": cfg.initial_location,
        "normal_terminal": cfg.normal_terminal,
        "failure_terminal": cfg.failure_terminal,
        "locations": locations,
        "transition_groups": transitions,
    }

