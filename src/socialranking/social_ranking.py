"""Core social ranking data structure representing total preorders of elements."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Hashable, Iterable, TypeAlias

from socialranking.power_relation import _element_sort_key

Element: TypeAlias = Hashable
Rank: TypeAlias = tuple[Element, ...]


@dataclass(frozen=True, eq=False)
class SocialRanking:
    """Ordered equivalence classes of individual elements.
    A social ranking ranks individual elements from best to worst.
    Elements inside the same rank are considered indifferent/tied.
    """

    ranks: tuple[Rank, ...]

    def __post_init__(self) -> None:
        normalized_ranks: list[Rank] = []
        seen_elements: set[Element] = set()

        for rank_index, rank in enumerate(self.ranks):
            if not isinstance(rank, (list, tuple)):
                raise TypeError(f"rank at index {rank_index} must be a list or tuple")

            normalized_rank = tuple(rank)
            if not normalized_rank:
                raise ValueError(f"rank at index {rank_index} must not be empty")

            try:
                unique_rank_elements = set(normalized_rank)
            except TypeError as error:
                raise TypeError("elements must be hashable") from error

            if len(normalized_rank) != len(unique_rank_elements):
                raise ValueError("equivalence class must not contain duplicate elements")

            for element in normalized_rank:
                if element in seen_elements:
                    raise ValueError(f"duplicate element found: {element}")
                seen_elements.add(element)

            sorted_rank = tuple(sorted(normalized_rank, key=_element_sort_key))
            normalized_ranks.append(sorted_rank)

        object.__setattr__(self, "ranks", tuple(normalized_ranks))

    @classmethod
    def from_nested(cls, ranks: Iterable[Iterable[Any]]) -> SocialRanking:
        """Create a social ranking from nested Python iterables.
        Supports both 2-level nesting (`[[1], [2, 3], [4]]`) and 3-level nesting
        (`[[[1]], [[2, 3]], [[4]]]`).
        """
        ranks_list = [list(r) for r in ranks]

        # Determine nesting depth by checking if any item is a list
        is_triple_nested = False
        for r in ranks_list:
            for item in r:
                if isinstance(item, list):
                    is_triple_nested = True
                    break
            if is_triple_nested:
                break

        final_ranks: list[tuple[Element, ...]] = []
        for eq_class in ranks_list:
            class_elements: list[Element] = []
            for item in eq_class:
                if is_triple_nested:
                    if isinstance(item, (list, tuple)):
                        class_elements.extend(item)
                    else:
                        class_elements.append(item)
                else:
                    class_elements.append(item)
            final_ranks.append(tuple(class_elements))

        return cls(tuple(final_ranks))

    @classmethod
    def from_string(cls, value: str) -> SocialRanking:
        """Create a social ranking from compact notation.
        Supported examples:
            "1 > (2 ~ 3) > 4"
            "apple > banana ~ chocolate"
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
                raise ValueError(f"malformed parentheses in equivalence class: {class_str}")

            if has_open and has_close:
                class_str = class_str[1:-1].strip()
                if not class_str:
                    raise ValueError("empty equivalence class inside parentheses")

            element_strings = class_str.split("~")
            elements: list[Element] = []
            for elem_str in element_strings:
                elem_str = elem_str.strip()
                if not elem_str:
                    raise ValueError("empty element name found")

                if "(" in elem_str or ")" in elem_str or ">" in elem_str or "~" in elem_str:
                    raise ValueError(f"invalid character in element name: {elem_str}")

                if elem_str.isdigit():
                    elements.append(int(elem_str))
                else:
                    elements.append(elem_str)

            ranks.append(elements)

        return cls.from_nested(ranks)

    @property
    def elements(self) -> tuple[Element, ...]:
        """Unique elements appearing in the ranking."""
        elements = {
            element
            for rank in self.ranks
            for element in rank
        }
        return tuple(sorted(elements, key=_element_sort_key))

    def element_lookup(self, element: Element) -> int | None:
        """Return the rank index of an element, or None if it is missing.
        Indices are zero-based, so 0 is the best rank.
        """
        for index, rank in enumerate(self.ranks):
            if element in rank:
                return index
        return None

    def compare(self, first: Element, second: Element) -> int:
        """Compare two elements.
        Returns:
            1 if first is strictly better than second
            0 if they are indifferent
            -1 if first is strictly worse than second
        """
        first_index = self.element_lookup(first)
        second_index = self.element_lookup(second)

        if first_index is None or second_index is None:
            raise ValueError("both elements must appear in the social ranking")
        if first_index < second_index:
            return 1
        if first_index > second_index:
            return -1
        return 0

    def strictly_prefers(self, first: Element, second: Element) -> bool:
        """Return whether `first` is strictly preferred to `second`."""
        return self.compare(first, second) == 1

    def weakly_prefers(self, first: Element, second: Element) -> bool:
        """Return whether `first` is at least as good as `second`."""
        return self.compare(first, second) >= 0

    def elements_are_indifferent(self, first: Element, second: Element) -> bool:
        """Return whether two existing elements are in the same rank."""
        first_index = self.element_lookup(first)
        second_index = self.element_lookup(second)

        if first_index is None or second_index is None:
            return False

        return first_index == second_index

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SocialRanking):
            return NotImplemented

        if len(self.ranks) != len(other.ranks):
            return False

        return all(
            set(r1) == set(r2)
            for r1, r2 in zip(self.ranks, other.ranks, strict=True)
        )

    def __hash__(self) -> int:
        return hash(tuple(frozenset(rank) for rank in self.ranks))

    def __str__(self) -> str:
        if not self.ranks:
            return ""

        formatted_ranks: list[str] = []
        for rank in self.ranks:
            if len(rank) == 1:
                formatted_ranks.append(str(rank[0]))
            else:
                formatted_ranks.append(f"({' ~ '.join(str(e) for e in rank)})")

        return " > ".join(formatted_ranks)
