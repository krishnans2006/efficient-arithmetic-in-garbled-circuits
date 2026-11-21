"""Load plaintext switch-system test cases from JSON."""

import json
from pathlib import Path

from .main import Constraint, Solver, Wire


def load_case(
    path: str | Path,
) -> tuple[Solver, dict[str, Wire], dict[str, int | None]]:
    """Return a fresh solver, named wires, and expected values without solving."""
    with Path(path).open() as stream:
        case = json.load(stream)

    wires = {}
    for specification in case["wires"]:
        name = specification["name"]
        if name in wires:
            raise ValueError(f"Duplicate wire name: {name}")
        wires[name] = Wire(**specification)

    def lookup(name):
        if name not in wires:
            raise ValueError(f"Unknown wire: {name}")
        return wires[name]

    solver = Solver()
    for index, specification in enumerate(case["constraints"]):
        arguments = dict(specification)
        kind = arguments.pop("type")
        try:
            constraint_type = Constraint[kind]
        except KeyError:
            raise ValueError(f"Constraint {index}: unknown type {kind!r}") from None

        for field in ("a", "b", "control", "output"):
            if field in arguments:
                arguments[field] = lookup(arguments[field])
        if "coefficients" in arguments:
            arguments["coefficients"] = {
                lookup(name): coefficient
                for name, coefficient in arguments["coefficients"].items()
            }
        solver.add_constraint(constraint_type, **arguments)

    expected = case["expected"]
    if not expected:
        raise ValueError("A test case must contain expected wire values")
    for name in expected:
        lookup(name)
    return solver, wires, expected
