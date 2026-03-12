"""Simple type checker with generics."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Type:
    name: str
    params: list[Type] = field(default_factory=list)

    def __eq__(self, other):
        if not isinstance(other, Type):
            return False
        return self.name == other.name and self.params == other.params

    def __hash__(self):
        return hash((self.name, tuple(self.params)))

    def __repr__(self):
        if self.params:
            params_str = ", ".join(repr(p) for p in self.params)
            return f"{self.name}[{params_str}]"
        return self.name


class TypeChecker:
    """Simple type checker with unification."""

    def __init__(self):
        self.substitutions: dict[str, Type] = {}

    def check(self, expected: Type, actual: Type) -> bool:
        """Check if actual matches expected type."""
        expected = self._resolve(expected)
        actual = self._resolve(actual)

        # Type variables (start with uppercase T)
        if expected.name.startswith("T") and len(expected.name) <= 2:
            # Bug: doesn't unify — just checks if already bound
            if expected.name in self.substitutions:
                return self.substitutions[expected.name] == actual
            return True  # Bug: should bind the type variable

        if actual.name.startswith("T") and len(actual.name) <= 2:
            if actual.name in self.substitutions:
                return self.substitutions[actual.name] == expected
            return True

        # Concrete types must match name and param count
        if expected.name != actual.name:
            return False
        if len(expected.params) != len(actual.params):
            return False

        return all(
            self.check(ep, ap)
            for ep, ap in zip(expected.params, actual.params)
        )

    def _resolve(self, t: Type) -> Type:
        """Resolve type variables using current substitutions."""
        if t.name in self.substitutions:
            return self._resolve(self.substitutions[t.name])
        if t.params:
            return Type(t.name, [self._resolve(p) for p in t.params])
        return t
