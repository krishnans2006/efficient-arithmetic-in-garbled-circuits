from enum import Enum

class Constraint(Enum):
    JOIN = 1
    SWITCH = 2
    ADD = 3
class Solver:
    def __init__(self, mod):
        self.m = mod
        self.values = {}
        self.constraints = []
        
    def wire(self, name, value = None):
        if name in self.values:
            raise ValueError(f"Wire {name} already exists")

        self.values[name] = value % self.m if value is not None else None
        return name

    def set(self, name, value):
        value %= self.m
        old = self.values[name]
        if old is not None and old != value:
            raise ValueError(f"Conflict on {name}: {old} != {value}")
        self.values[name] = value

    def add_constraint(self, constraint_type: Constraint, a=None, b=None, control = None, inputs=None, output = None):
        match constraint_type:
            case Constraint.JOIN:
                if a is None or b is None:
                    raise ValueError("Join requires both a and b")
                self.constraints.append((Constraint.JOIN, a, b))
            case Constraint.SWITCH:
                if a is None or control is None or b is None:
                    raise ValueError("Join requires both a, b, and control")
                self.constraints.append((Constraint.SWITCH, a, control, b))
            case Constraint.ADD:
                if not inputs or output is None:
                    raise ValueError("Add requires both inputs and an output")
                self.constraints.append((Constraint.ADD, inputs, output))

    def solve(self):
        while True:
            before = self.values.copy()
            for constraint in self.constraints:
                match constraint[0]:
                    case Constraint.JOIN:
                        a,b = constraint[1:]
                        if self.values[a] is not None:
                            self.set(b, self.values[a])
                        if self.values[b] is not None:
                            self.set(a, self.values[b])
                    case Constraint.SWITCH:
                        a, control, b = constraint[1:]
                        c = self.values[control]
                        if c == 0:
                            if self.values[a] is not None:
                                self.set(b, self.values[a])
                            if self.values[b] is not None:
                                self.set(a, self.values[b])
                    case Constraint.ADD:
                        inputs, output = constraint[1:]
                        num_nones = [self.values[i] for i in inputs].count(None)
                        if num_nones == 0:
                            self.set(output, sum(self.values[i] for i in inputs))
                        elif num_nones == 1 and self.values[output] is not None:
                            index = [i for i in inputs if self.values[i] is None][0]
                            self.set(index, self.values[output] - sum(self.values[i] for i in inputs if self.values[i] is not None))
            if self.values == before:
                break

        return self.values


s = Solver(mod=4)

h = [s.wire(f"h{i}", int(i == 2)) for i in range(4)]
zero = s.wire("zero", 0)
y = [s.wire(f"y{i}") for i in range(4)]

scalar = s.wire("scalar")     # Unknown initially
input_scalar = s.wire("input_scalar", 3)

for i in range(4):
    s.add_constraint(constraint_type=Constraint.SWITCH, a=zero, control=h[i], b=y[i])

s.add_constraint(constraint_type=Constraint.ADD, inputs=y, output=scalar)
s.add_constraint(constraint_type=Constraint.JOIN, a=scalar, b=input_scalar)

print(s.solve())
print("scaled vector:", [s.values[w] for w in y])
