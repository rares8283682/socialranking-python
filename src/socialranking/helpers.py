"""Small reusable helper functions across the library."""
from __future__ import annotations

from itertools import combinations
from typing import Hashable, Iterable


Element = Hashable #we stick to hashable elements for now
Coalition = tuple[Element, ...] #it can be of any length


def create_powerset(elements: Iterable[Element], include_empty_set: bool = True) -> list[Coalition]:
    """Return all coalitions ordered from largest to smallest.

    This function is intended for small or moderate element sets because the
    number of coalitions grows exponentially. For 20 elements, the full
    powerset already contains more than 1 million coalitions.

    The order is not only largest to smallest. Inside each size, the order
    follows the original input order.

    Example:
        create_powerset(["a", "b", "c"])
        returns:
        [("a", "b", "c"), ("a", "b"), ("a", "c"), ("b", "c"), ("a",), ("b",), ("c",), ()]

    If include_empty_set is False, the empty coalition is omitted.
    The result has length 2**n if include_empty_set is True, otherwise 2**n - 1.
    """

    items = list(elements)
    
    try:
        unique_items = set(items)
    except TypeError as error:
        raise TypeError("elements must be hashable") from error

    if len(items) != len(set(items)):
        raise ValueError("elements must not contain duplicates")
    coalitions: list[Coalition] = []

    for size in range(len(items), 0, -1):
        coalitions.extend(tuple(combination) for combination in combinations(items, size))

    if include_empty_set:
        coalitions.append(())

    return coalitions
