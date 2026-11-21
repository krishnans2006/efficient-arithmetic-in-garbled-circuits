from enum import Enum


class Constraint(Enum):
    JOIN = 1
    SWITCH = 2
    AFFINE = 3
    MOD = 4
    DIV = 5


class Wire:
    def __init__(self, name: str, k: int, value: int | None = None):
        if k < 1:
            raise ValueError("Wire width must be at least 1")

        self.name = name
        self.k = k
        self.value = None

        if value is not None:
            self.set(value)

    def set(self, value):
        value %= 1 << self.k
        if self.value is not None and self.value != value:
            raise ValueError(f"Conflict on {self.name}: {self.value} != {value}")
        changed = self.value is None
        self.value = value
        return changed

    def __repr__(self):
        return f"({self.name}, {self.k}, {self.value})"


class Solver:
    def __init__(self):
        self.constraints = []
        self.wires = set()

    def add_constraint(
        self,
        constraint_type: Constraint,
        a=None,
        b=None,
        control=None,
        coefficients=None,
        constant=None,
        output=None,
    ):
        match constraint_type:
            case Constraint.JOIN:
                if a is None or b is None:
                    raise ValueError("Join requires both a and b")
                if a.k != b.k:
                    raise ValueError("Join requires matching wire widths")

                self.constraints.append((Constraint.JOIN, a, b))
                self.wires.update((a, b))
            case Constraint.SWITCH:
                if a is None or control is None or b is None:
                    raise ValueError("Switch requires both a, b, and control")

                if a.k != b.k or control.k != 1:
                    raise ValueError(
                        "Switch requires matching wire widths and control to have 1-bit width"
                    )
                self.constraints.append((Constraint.SWITCH, a, control, b))
                self.wires.update((a, control, b))
            case Constraint.AFFINE:
                if coefficients is None or constant is None or output is None:
                    raise ValueError(
                        "Affine requires coefficients, a constant, and an output"
                    )
                if any(wire.k != output.k for wire in coefficients):
                    raise ValueError("Affine requires matching wire widths")
                self.constraints.append(
                    (Constraint.AFFINE, dict(coefficients), constant, output)
                )
                self.wires.update(coefficients)
                self.wires.add(output)
            case Constraint.MOD | Constraint.DIV:
                if a is None or output is None:
                    raise ValueError("Mod/div requires input and output wires")
                if a.k < output.k:
                    raise ValueError("Mod/div cannot increase wire width")

                self.constraints.append((constraint_type, a, output))
                self.wires.update((a, output))
            case _:
                raise ValueError(f"Unknown constraint type: {constraint_type}")

    def solve(self):
        while True:
            changed = False
            for constraint in self.constraints:
                match constraint[0]:
                    case Constraint.JOIN:
                        a, b = constraint[1:]
                        if a.value is not None:
                            changed |= b.set(a.value)
                        if b.value is not None:
                            changed |= a.set(b.value)
                    case Constraint.SWITCH:
                        a, control, b = constraint[1:]
                        c = control.value
                        if c == 0:
                            if a.value is not None:
                                changed |= b.set(a.value)
                            if b.value is not None:
                                changed |= a.set(b.value)
                    case Constraint.AFFINE:
                        coefficients, constant, output = constraint[1:]

                        modulus = 1 << output.k
                        unknown = [wire for wire in coefficients if wire.value is None]

                        known_sum = (
                            constant
                            + sum(
                                coefficient * wire.value
                                for wire, coefficient in coefficients.items()
                                if wire.value is not None
                            )
                        ) % modulus
                        if len(unknown) == 0:
                            changed |= output.set(known_sum)
                        elif len(unknown) == 1 and output.value is not None:
                            unknown_wire = unknown[0]
                            coefficient = coefficients[unknown_wire] % modulus

                            remainder = (output.value - known_sum) % modulus
                            inverse = pow(coefficient, -1, modulus)
                            changed |= unknown_wire.set(remainder * inverse)
                    case Constraint.MOD:
                        a, output = constraint[1:]
                        if a.value is not None:
                            changed |= output.set(a.value)

                    case Constraint.DIV:
                        a, output = constraint[1:]
                        if a.value is not None:
                            shift = a.k - output.k
                            changed |= output.set(a.value >> shift)
            if not changed:
                break

        return {wire: wire.value is not None for wire in self.wires}
