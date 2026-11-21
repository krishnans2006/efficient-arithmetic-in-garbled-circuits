# Efficient Arithmetic in Garbled Circuits

An Implementation of [Efficient Arithmetic in Garbled Circuits](https://doi.org/10.1007/978-3-031-58740-5_1).

## Running tests

Install [uv](https://docs.astral.sh/uv/) and run:

```sh
uv sync
uv run pytest
```

## JSON test cases

Add a `.json` file to `tests/cases/`. Conveniently, pytest discovers each file automatically.
Start by copying `tests/cases/scale_mod_div.json`, which contains the original
example: scale a one-hot vector by 100, reduce modulo 64, then divide by 4.
The selected entry becomes `100`, then `36`, then `9`.

Each case has three required fields:

- `wires`: a list of objects with a unique `name`, bit width `k`, and optional
  `value`. Omit `value` or use `null` for an unknown wire. Initial values are
  reduced modulo `2**k`.
- `constraints`: a list of gates, using the uppercase `type` names below.
  Reference wires by name; the loader resolves names to `Wire` objects.
- `expected`: a dictionary mapping wire names to expected final values. Only
  listed wires are checked. Use `null` to check that a wire remains unknown.

| Type | Required fields besides `type` |
| --- | --- |
| `JOIN` | `a`, `b` |
| `SWITCH` | `a`, `control`, `b` |
| `AFFINE` | `coefficients` (wire name to integer coefficient), `constant`, `output` |
| `MOD` | `a`, `output` |
| `DIV` | `a`, `output` |

For example, this case checks `12 / 4 = 3`:

```json
{
  "wires": [
    {"name": "x", "k": 4, "value": 12},
    {"name": "y", "k": 2}
  ],
  "constraints": [
    {"type": "DIV", "a": "x", "output": "y"}
  ],
  "expected": {"y": 3}
}
```