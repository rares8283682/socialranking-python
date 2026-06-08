# Core social ranking data structure representing total preorders of elements.

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Hashable, Iterable, TypeAlias, Mapping, Tuple, Sequence
from collections.abc import Iterable as CollIterable
from socialranking.power_relation import _element_sort_key

Element: TypeAlias = Hashable
Rank: TypeAlias = Tuple[Element, ...]


class _ImmutableTuple(tuple):
    """Immutable tuple subclass that raises ``AttributeError`` on mutation attempts.
    Used for inner ranks so that attempts to modify an element raise ``AttributeError``
    (as required by the test suite).
    """

    def __new__(cls, iterable):
        return super().__new__(cls, tuple(iterable))

    def __setitem__(self, *_, **__):
        raise AttributeError("ranks is immutable")

    def __delitem__(self, *_, **__):
        raise AttributeError("ranks is immutable")


class _ImmutableDict(dict):
    """Read‑only dict that raises ``AttributeError`` on any mutation."""

    def __setitem__(self, *_, **__):
        raise AttributeError("element_index is immutable")

    def __delitem__(self, *_, **__):
        raise AttributeError("element_index is immutable")

    def clear(self, *_, **__):
        raise AttributeError("element_index is immutable")

    def pop(self, *_, **__):
        raise AttributeError("element_index is immutable")

    def popitem(self, *_, **__):
        raise AttributeError("element_index is immutable")

    def setdefault(self, *_, **__):
        raise AttributeError("element_index is immutable")

    def update(self, *_, **__):
        raise AttributeError("element_index is immutable")


def _flatten_all(item: Any) -> list[Element]:
    """Recursively flatten any nested iterable (list, tuple, set) into a flat list.
    Strings are treated as atomic values.
    """
    if isinstance(item, (list, tuple, set)):
        result: list[Element] = []
        for sub in item:
            result.extend(_flatten_all(sub))
        return result
    return [item]


@dataclass(frozen=True, eq=False)
class SocialRanking:
    """Ordered equivalence classes of individual elements.
    Elements inside the same rank are considered indifferent/tied.
    """

    ranks: Tuple[Rank, ...]
    _element_index: Mapping[Element, int] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Validate and normalise the ranking.
        - Every rank must be iterable.
        - No rank may be empty.
        - All elements must be hashable.
        - No duplicate elements across ranks.
        - Each rank is sorted deterministically using ``_element_sort_key``.
        - ``ranks`` becomes a plain ``tuple`` of ``_ImmutableTuple`` ranks.
        - ``_element_index`` becomes a read‑only mapping.
        """

        normalized: list[_ImmutableTuple] = []
        seen: set[Element] = set()

        for i, rank in enumerate(self.ranks):
            if not isinstance(rank, CollIterable):
                raise TypeError("must be an iterable")

            rank_tuple = tuple(rank)
            if not rank_tuple:
                raise ValueError(f"rank at index {i} must not be empty")

            try:
                uniq = set(rank_tuple)
            except TypeError as exc:
                raise TypeError("elements must be hashable") from exc

            if len(uniq) != len(rank_tuple):
                raise ValueError("duplicate element found")

            overlap = seen.intersection(uniq)
            if overlap:
                raise ValueError("duplicate element found")
            seen.update(uniq)

            sorted_rank = tuple(sorted(rank_tuple, key=_element_sort_key))
            normalized.append(_ImmutableTuple(sorted_rank))

        object.__setattr__(self, "ranks", _ImmutableTuple(normalized))

        # Build element → rank index map.
        element_index: dict[Element, int] = {}
        for rank_idx, rank in enumerate(normalized):
            for el in rank:
                element_index[el] = rank_idx
        object.__setattr__(self, "_element_index", _ImmutableDict(element_index))

    @classmethod
    def _build_without_sort(cls, ranks_list: list[list[Element]]) -> "SocialRanking":
        """Create a ``SocialRanking`` from already‑ordered ranks without sorting.
        Used by ``from_string`` where textual order must be preserved.
        """
        normalized: list[_ImmutableTuple] = []
        seen: set[Element] = set()
        for i, rank in enumerate(ranks_list):
            if not isinstance(rank, CollIterable):
                raise TypeError("must be an iterable")
            rank_tuple = tuple(rank)
            if not rank_tuple:
                raise ValueError(f"rank at index {i} must not be empty")
            try:
                uniq = set(rank_tuple)
            except TypeError as exc:
                raise TypeError("elements must be hashable") from exc
            if len(uniq) != len(rank_tuple):
                raise ValueError("duplicate element found")
            overlap = seen.intersection(uniq)
            if overlap:
                raise ValueError("duplicate element found")
            seen.update(uniq)
            normalized.append(_ImmutableTuple(rank_tuple))

        obj = object.__new__(cls)
        object.__setattr__(obj, "ranks", tuple(normalized))
        element_index: dict[Element, int] = {}
        for rank_idx, rank in enumerate(normalized):
            for el in rank:
                element_index[el] = rank_idx
        object.__setattr__(obj, "_element_index", _ImmutableDict(element_index))
        return obj

    @classmethod
    def from_nested(cls, ranks: Iterable[Iterable[Any]]) -> "SocialRanking":
        """Create a ``SocialRanking`` from nested iterables.
        All nesting levels are recursively flattened so that each rank ends up as a
        flat collection of hashable elements.
        """
        outer = list(ranks)
        final_ranks: list[list[Element]] = []
        for eq_class in outer:
            # Validate that each rank is itself iterable before flattening.
            if not isinstance(eq_class, CollIterable):
                raise TypeError("must be an iterable")
            # Recursively flatten all nesting levels so that every rank ends up
            # as a flat list of leaf elements (strings and non-iterables are kept as-is).
            # e.g. [[1, 2]] → [1, 2], [[[6]]] → [6]
            final_ranks.append(_flatten_all(eq_class))
        # ``SocialRanking`` will sort each rank and validate hashability in ``__post_init__``.
        return cls(tuple(tuple(r) for r in final_ranks))

    @classmethod
    def from_string(cls, value: str) -> "SocialRanking":
        """Parse a compact social ranking string.
        Preserves element order; supports negative ints and non‑numeric strings.
        """
        if not isinstance(value, str):
            raise TypeError("value must be a string")
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("social ranking string must not be empty")

        class_strings = cleaned.split(">")
        ranks: list[list[Element]] = []

        for class_str in class_strings:
            class_str = class_str.strip()
            if not class_str:
                raise ValueError("empty equivalence class found in string")

            has_open = class_str.startswith("(")
            has_close = class_str.endswith(")")
            if has_open != has_close:
                raise ValueError("malformed parentheses")

            if has_open and has_close:
                inner = class_str[1:-1].strip()
                if '(' in inner or ')' in inner:
                    raise ValueError("malformed parentheses")
                if '~' not in inner:
                    raise ValueError("malformed parentheses")
                class_str = inner

            element_strings = class_str.split("~")
            elements: list[Element] = []
            for elem_str in element_strings:
                elem_str = elem_str.strip()
                if not elem_str:
                    raise ValueError("empty element name found")
                if any(ch in elem_str for ch in "(),>~"):
                    raise ValueError("invalid character")
                if elem_str.lstrip('-').isdigit():
                    elements.append(int(elem_str))
                else:
                    elements.append(elem_str)
            ranks.append(elements)
        # Preserve order without sorting.
        return cls._build_without_sort(ranks)

    @property
    def elements(self) -> Tuple[Element, ...]:
        if not hasattr(self, "_cached_elements"):
            unique = {e for rank in self.ranks for e in rank}
            object.__setattr__(self, "_cached_elements", tuple(sorted(unique, key=_element_sort_key)))
        return self._cached_elements

    def element_lookup(self, element: Element) -> int | None:
        """Return the rank index of ``element`` or ``None`` if absent."""
        return self._element_index.get(element)

    def compare(self, first: Element, second: Element) -> int:
        """Compare two elements.
        Returns ``1`` if ``first`` is strictly preferred, ``0`` if indifferent,
        ``-1`` if ``first`` is less preferred.
        """
        first_idx = self.element_lookup(first)
        second_idx = self.element_lookup(second)
        if first_idx is None or second_idx is None:
            raise ValueError("both elements must appear in the social ranking")
        if first_idx < second_idx:
            return 1
        if first_idx > second_idx:
            return -1
        return 0

    def strictly_prefers(self, first: Element, second: Element) -> bool:
        return self.compare(first, second) == 1

    def weakly_prefers(self, first: Element, second: Element) -> bool:
        return self.compare(first, second) >= 0

    def elements_are_indifferent(self, first: Element, second: Element) -> bool:
        try:
            return self.compare(first, second) == 0
        except ValueError:
            return False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SocialRanking):
            return NotImplemented
        self_canonical = tuple(frozenset(rank) for rank in self.ranks)
        other_canonical = tuple(frozenset(rank) for rank in other.ranks)
        return self_canonical == other_canonical

    def __hash__(self) -> int:
        return hash(tuple(frozenset(rank) for rank in self.ranks))

    def __str__(self) -> str:
        if not self.ranks:
            return ""
        formatted: list[str] = []
        for rank in self.ranks:
            if len(rank) == 1:
                formatted.append(str(rank[0]))
            else:
                formatted.append(f"({" ~ ".join(str(e) for e in rank)})")
        return " > ".join(formatted)
