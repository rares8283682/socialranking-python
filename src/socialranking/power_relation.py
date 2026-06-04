"""Core power relation data structure."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable


Element = Hashable
Coalition = tuple[Element, ...]
EquivalenceClass = tuple[Coalition, ...]


@dataclass(frozen=True)
class PowerRelation:
    """Ordered equivalence classes of coalitions.

    This is the Python equivalent of the R `PowerRelation()` object.
    Implementation will be added in the first porting milestone.
    """

    equivalence_classes: tuple[EquivalenceClass, ...]

    @classmethod
    def from_nested(cls, equivalence_classes: list[list[list[Element]]]) -> "PowerRelation":
        """Create a power relation from nested Python lists."""
        normalized = tuple(
            tuple(tuple(sorted(coalition)) for coalition in equivalence_class)
            for equivalence_class in equivalence_classes
        )
        return cls(normalized)
