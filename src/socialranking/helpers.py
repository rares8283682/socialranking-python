"""Small reusable helper functions."""

from __future__ import annotations

from itertools import combinations
from typing import Hashable, Iterable


Element = Hashable
Coalition = tuple[Element, ...]


def create_powerset(elements: Iterable[Element], include_empty_set: bool = True) -> list[Coalition]:
    """Return coalitions ordered from largest to smallest, matching the R helper."""
    items = list(elements)
    coalitions: list[Coalition] = []

    for size in range(len(items), 0, -1):
        coalitions.extend(tuple(combination) for combination in combinations(items, size))

    if include_empty_set:
        coalitions.append(())

    return coalitions
