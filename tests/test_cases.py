import json
from pathlib import Path

import pytest

from src.cases import load_case
from src.main import Constraint, Solver, Wire

CASES = sorted((Path(__file__).parent / "cases").glob("*.json"))


@pytest.mark.parametrize("path", CASES, ids=lambda path: path.stem)
def test_json_case(path):
    solver, wires, expected = load_case(path)
    solver.solve()
    assert {name: wires[name].value for name in expected} == expected


def test_cases_have_independent_state():
    path = Path(__file__).parent / "cases" / "scale_mod_div.json"
    first, first_wires, _ = load_case(path)
    second, second_wires, expected = load_case(path)
    first.solve()
    assert first_wires["y2"].value == 100
    assert second_wires["y2"].value is None
    second.solve()
    assert {name: second_wires[name].value for name in expected} == expected


@pytest.mark.parametrize("kind", list(Constraint))
def test_invalid_widths_are_rejected(kind):
    a, b = Wire("a", 4), Wire("b", 3)
    arguments = {
        Constraint.JOIN: {"a": a, "b": b},
        Constraint.SWITCH: {"a": a, "b": b, "control": Wire("control", 1)},
        Constraint.AFFINE: {"coefficients": {a: 1}, "constant": 0, "output": b},
        Constraint.MOD: {"a": b, "output": a},
        Constraint.DIV: {"a": b, "output": a},
    }
    with pytest.raises(ValueError, match="width"):
        Solver().add_constraint(kind, **arguments[kind])


def test_conflicting_assignment_is_rejected():
    solver = Solver()
    solver.add_constraint(Constraint.JOIN, a=Wire("a", 3, 1), b=Wire("b", 3, 2))
    with pytest.raises(ValueError, match="Conflict"):
        solver.solve()


@pytest.mark.parametrize("problem", ["duplicate", "reference", "type", "expected"])
def test_invalid_json_case(tmp_path, problem):
    case = {
        "wires": [{"name": "x", "k": 2}],
        "constraints": [],
        "expected": {"x": None},
    }
    if problem == "duplicate":
        case["wires"].append({"name": "x", "k": 2})
    elif problem == "reference":
        case["constraints"] = [{"type": "JOIN", "a": "x", "b": "missing"}]
    elif problem == "type":
        case["constraints"] = [{"type": "TYPO"}]
    else:
        case["expected"] = {"missing": 0}
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(case))
    with pytest.raises(ValueError):
        load_case(path)
