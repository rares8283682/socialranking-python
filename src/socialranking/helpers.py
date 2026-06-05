"""Small reusable helper functions across the library."""
"""This function tries to build the coalitions"""
""" If you set the include_empty_set=False, then the empty coalition will be not printed
    The result has length 2**n if `include_empty_set` is True, otherwise 2**n - 1."""
from __future__ import annotations

from itertools import combinations
from typing import Hashable, Iterable


Element = Hashable #we stick to hashable elements for now
Coalition = tuple[Element, ...] #it can be of any length


def create_powerset(elements: Iterable[Element], include_empty_set: bool = True) -> list[Coalition]:
    """Return coalitions ordered from largest to smallest"""
    items = list(elements)
    if len(items) != len(set(items)):
        raise ValueError("elements must not contain duplicates")
    coalitions: list[Coalition] = []

    for size in range(len(items), 0, -1):
        coalitions.extend(tuple(combination) for combination in combinations(items, size))

    if include_empty_set:
        coalitions.append(())

    return coalitions
