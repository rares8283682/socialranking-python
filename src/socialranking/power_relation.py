"""Represent power relations as ordered equivalence classes of coalitions."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Hashable


Element = Hashable
Coalition = tuple[Element, ...]
EquivalenceClass = tuple[Coalition, ...]
LookupIndex = int | None
ElementLocation = tuple[int, int]


@dataclass(frozen=True)
class PowerRelation:
    """Ordered equivalence classes of coalitions.

    A power relation ranks coalitions from best to worst.

    Example:
        12 > 1 ~ 2 > {}

    means:
        coalition {1, 2} is better than coalitions {1} and {2},
        which are tied, and both are better than the empty coalition.
    """

    equivalence_classes: tuple[EquivalenceClass, ...]

    def __post_init__(self) -> None:
        normalized = _normalize_equivalence_classes(self.equivalence_classes)
        object.__setattr__(self, "equivalence_classes", normalized)

    @classmethod
    def from_nested(cls, equivalence_classes: list[list[list[Element]]]) -> "PowerRelation":
        """Create a power relation from nested Python lists.

        Example:
            PowerRelation.from_nested([
                [[1, 2]],
                [[1], [2]],
                [[]],
            ])

        represents:
            12 > (1 ~ 2) > {}
        """

        return cls(
            tuple(
                tuple(tuple(coalition) for coalition in equivalence_class)
                for equivalence_class in equivalence_classes
            )
        )

    @classmethod
    def from_string(cls, value: str) -> "PowerRelation":
        """Create a power relation from a compact string.

        Supported examples:
            "12 > 1 > 2"
            "12 > 1 ~ 2 > {}"
            "ab > a > b"
            "(1 ~ 2) > {}"

        Important:
            This compact parser reads every character as one element.
            Therefore "10" is interpreted as coalition {1, 0}, not element 10.
        """

        if not isinstance(value, str):
            raise TypeError("power relation value must be a string")

        tokens = _tokenize_power_relation_string(value)

        if not tokens:
            raise ValueError("power relation string must contain at least one coalition")

        equivalence_classes: list[list[list[Element]]] = []
        current_class: list[list[Element]] = []
        current_coalition: list[Element] | None = None

        expecting_coalition = True

        for token in tokens:
            if token == ">":
                if expecting_coalition:
                    raise ValueError("malformed power relation string")

                assert current_coalition is not None
                current_class.append(current_coalition)
                equivalence_classes.append(current_class)

                current_class = []
                current_coalition = None
                expecting_coalition = True

            elif token == "~":
                if expecting_coalition:
                    raise ValueError("malformed power relation string")

                assert current_coalition is not None
                current_class.append(current_coalition)

                current_coalition = None
                expecting_coalition = True

            else:
                if not expecting_coalition:
                    raise ValueError("missing separator between coalitions")

                current_coalition = _parse_coalition_token(token)
                expecting_coalition = False

        if expecting_coalition:
            raise ValueError("malformed power relation string")

        assert current_coalition is not None
        current_class.append(current_coalition)
        equivalence_classes.append(current_class)

        return cls.from_nested(equivalence_classes)

    @property
    def elements(self) -> tuple[Element, ...]:
        """Return unique elements appearing in the relation, sorted for stable output."""

        elements = {
            element
            for equivalence_class in self.equivalence_classes
            for coalition in equivalence_class
            for element in coalition
        }

        return tuple(sorted(elements, key=_element_sort_key))

    @property
    def coalitions(self) -> tuple[Coalition, ...]:
        """Return all coalitions in the relation, from best class to worst class."""

        return tuple(
            coalition
            for equivalence_class in self.equivalence_classes
            for coalition in equivalence_class
        )

    def coalition_lookup(
        self,
        coalition: list[Element] | tuple[Element, ...] | Element,
    ) -> LookupIndex:
        """Return the zero-based equivalence-class index containing `coalition`.

        Lower index means better coalition.

        Returns:
            int | None
        """

        key = _coerce_coalition(coalition)

        for index, equivalence_class in enumerate(self.equivalence_classes):
            if key in equivalence_class:
                return index

        return None

    def coalition_position(
        self,
        coalition: list[Element] | tuple[Element, ...] | Element,
    ) -> tuple[int, int] | None:
        """Return the exact location of a coalition.

        Returns:
            (equivalence_class_index, coalition_index)

        or:
            None if the coalition does not appear.
        """

        key = _coerce_coalition(coalition)

        for equivalence_class_index, equivalence_class in enumerate(self.equivalence_classes):
            for coalition_index, existing_coalition in enumerate(equivalence_class):
                if key == existing_coalition:
                    return (equivalence_class_index, coalition_index)

        return None

    def element_lookup(self, element: Element) -> tuple[ElementLocation, ...]:
        """Return locations of coalitions containing `element`.

        Each location is:
            (equivalence_class_index, coalition_index)
        """

        locations: list[ElementLocation] = []

        for equivalence_class_index, equivalence_class in enumerate(self.equivalence_classes):
            for coalition_index, coalition in enumerate(equivalence_class):
                if element in coalition:
                    locations.append((equivalence_class_index, coalition_index))

        return tuple(locations)

    def compare(
        self,
        first: list[Element] | tuple[Element, ...] | Element,
        second: list[Element] | tuple[Element, ...] | Element,
    ) -> int:
        """Compare two coalitions.

        Returns:
            1  if first is strictly better than second
            0  if first and second are indifferent
            -1 if first is strictly worse than second

        Raises:
            ValueError if one of the coalitions is missing.
        """

        first_index = self.coalition_lookup(first)
        second_index = self.coalition_lookup(second)

        if first_index is None:
            raise ValueError(f"first coalition {first!r} is not in the power relation")

        if second_index is None:
            raise ValueError(f"second coalition {second!r} is not in the power relation")

        if first_index < second_index:
            return 1

        if first_index > second_index:
            return -1

        return 0

    def strictly_prefers(
        self,
        first: list[Element] | tuple[Element, ...] | Element,
        second: list[Element] | tuple[Element, ...] | Element,
    ) -> bool:
        """Return whether `first` is strictly better than `second`."""

        return self.compare(first, second) == 1

    def weakly_prefers(
        self,
        first: list[Element] | tuple[Element, ...] | Element,
        second: list[Element] | tuple[Element, ...] | Element,
    ) -> bool:
        """Return whether `first` is at least as good as `second`."""

        return self.compare(first, second) >= 0

    def coalitions_are_indifferent(
        self,
        first: list[Element] | tuple[Element, ...] | Element,
        second: list[Element] | tuple[Element, ...] | Element,
    ) -> bool:
        """Return whether two coalitions are in the same equivalence class.

        Missing coalitions are not treated as indifferent.
        """

        first_index = self.coalition_lookup(first)
        second_index = self.coalition_lookup(second)

        return first_index is not None and first_index == second_index

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PowerRelation):
            return NotImplemented

        if len(self.equivalence_classes) != len(other.equivalence_classes):
            return False

        return all(
            set(equivalence_class) == set(other_equivalence_class)
            for equivalence_class, other_equivalence_class in zip(
                self.equivalence_classes,
                other.equivalence_classes,
                strict=True,
            )
        )

    def __hash__(self) -> int:
        return hash(
            tuple(
                frozenset(equivalence_class)
                for equivalence_class in self.equivalence_classes
            )
        )

    def __str__(self) -> str:
        compact = self._uses_compact_format()
        formatted_classes: list[str] = []

        for equivalence_class in self.equivalence_classes:
            coalitions = [
                _format_coalition(coalition, compact)
                for coalition in equivalence_class
            ]

            if len(coalitions) == 1:
                formatted_classes.append(coalitions[0])
            else:
                formatted_classes.append(f"({' ~ '.join(coalitions)})")

        return " > ".join(formatted_classes)

    def _uses_compact_format(self) -> bool:
        return all(len(str(element)) == 1 for element in self.elements)


def _normalize_equivalence_classes(
    equivalence_classes: tuple[EquivalenceClass, ...],
) -> tuple[EquivalenceClass, ...]:
    if not equivalence_classes:
        raise ValueError("must supply at least one equivalence class")

    normalized: list[EquivalenceClass] = []
    seen_coalitions: set[Coalition] = set()

    for index, equivalence_class in enumerate(equivalence_classes):
        if not equivalence_class:
            raise ValueError(f"equivalence class at index {index} must not be empty")

        normalized_class: list[Coalition] = []

        for coalition in equivalence_class:
            normalized_coalition = _coerce_coalition(coalition)

            if normalized_coalition in seen_coalitions:
                raise ValueError("coalition must not appear more than once")

            seen_coalitions.add(normalized_coalition)
            normalized_class.append(normalized_coalition)

        normalized.append(tuple(normalized_class))

    return tuple(normalized)


def _coerce_coalition(
    coalition: list[Element] | tuple[Element, ...] | Element,
) -> Coalition:
    """Normalize a coalition.

    Lists and tuples are interpreted as coalitions.

    Single values are interpreted as one-element coalitions.

    Example:
        [2, 1] becomes (1, 2)
        1 becomes (1,)
        "a" becomes ("a",)
    """

    if isinstance(coalition, (list, tuple)):
        try:
            unique_elements = set(coalition)
        except TypeError as error:
            raise TypeError("coalition elements must be hashable") from error

        if len(coalition) != len(unique_elements):
            raise ValueError("coalition must not contain duplicate elements")

        return tuple(sorted(coalition, key=_element_sort_key))

    try:
        hash(coalition)
    except TypeError as error:
        raise TypeError("coalition must be hashable or a list/tuple of hashable elements") from error

    return (coalition,)


def _element_sort_key(element: Element) -> tuple[str, str]:
    return (type(element).__name__, repr(element))


def _format_coalition(coalition: Coalition, compact: bool) -> str:
    if not coalition:
        return "{}"

    if compact:
        return "".join(str(element) for element in coalition)

    return "{" + ", ".join(str(element) for element in coalition) + "}"


def _tokenize_power_relation_string(value: str) -> list[str]:
    """Tokenize a compact power relation string.

    Removes whitespace and parentheses.

    Keeps:
        >
        ~
        {}
        alphanumeric coalition tokens
    """

    stripped = value.replace(" ", "")
    stripped = stripped.replace("(", "")
    stripped = stripped.replace(")", "")

    if not stripped:
        raise ValueError("power relation string must contain at least one coalition")

    token_pattern = r"\{\}|[0-9a-zA-Z]+|>|~"
    tokens = re.findall(token_pattern, stripped)

    reconstructed = "".join(tokens)

    if reconstructed != stripped:
        raise ValueError(f"invalid character in power relation string: {value!r}")

    return tokens


def _parse_coalition_token(token: str) -> list[Element]:
    if token == "{}":
        return []

    coalition: list[Element] = []

    for char in token:
        if char.isdigit():
            coalition.append(int(char))
        else:
            coalition.append(char)

    return coalition
