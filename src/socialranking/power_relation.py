"""Power relation representation for ordered coalitions."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Hashable, Iterable, TypeAlias


Element: TypeAlias = Hashable
Coalition: TypeAlias = tuple[Element, ...]
EquivalenceClass: TypeAlias = tuple[Coalition, ...]
CoalitionInput: TypeAlias = list[Element] | tuple[Element, ...] | Element
LookupIndex: TypeAlias = int | None
ElementLocation: TypeAlias = tuple[int, int]


class PowerRelation:
    """Ordered equivalence classes of coalitions.
    A power relation ranks coalitions from best to worst. Coalitions inside the
    same equivalence class are considered equally good.

    Parameters
    ----------
    equivalence_classes : iterable of equivalence classes
        Each equivalence class is an iterable of coalitions.
    elements : set, optional
        If provided together with an empty *equivalence_classes*, the relation
        is treated as having zero equivalence classes but the given elements.
    """

    __slots__ = ('equivalence_classes', '_explicit_elements')

    def __init__(self, equivalence_classes: tuple[EquivalenceClass, ...] | list = (),*,elements: set[Element] | None = None,) -> None:
        eq_input = tuple(equivalence_classes)

        if not eq_input and elements is not None:
            #no equivalence classes but explicit element set.
            normalized: tuple[EquivalenceClass, ...] = ()
            object.__setattr__(self, 'equivalence_classes', normalized)
            sorted_elems = tuple(sorted(elements, key=_element_sort_key))
            object.__setattr__(self, '_explicit_elements', sorted_elems)
        else:
            normalized = _normalize_equivalence_classes(eq_input)
            object.__setattr__(self, 'equivalence_classes', normalized)
            object.__setattr__(self, '_explicit_elements', None)

    @classmethod
    def from_nested(cls, equivalence_classes: Iterable[Iterable[Iterable[Element]]]) -> PowerRelation:
        """Create a power relation from nested Python iterables.
        Example:
            PowerRelation.from_nested([
                [[1, 2]],
                [[1], [2]],
                [[]],
            ])
        """
        normalized_input: list[EquivalenceClass] = []

        for equivalence_class_index, equivalence_class in enumerate(equivalence_classes):
            normalized_class: list[Coalition] = []

            for coalition in equivalence_class:
                if not isinstance(coalition, (list, tuple)):
                    raise TypeError(
                        "from_nested expects each coalition to be a list or tuple; "
                        f"invalid coalition in equivalence class {equivalence_class_index}"
                    )
                normalized_class.append(tuple(coalition))

            normalized_input.append(tuple(normalized_class))

        return cls(tuple(normalized_input))

    @classmethod
    def from_string(cls, value: str) -> PowerRelation:
        """Create a power relation from compact notation.
        Supported examples:
            "12 > 1 > 2"
            "12 > (1 ~ 2) > {}"
        Digits are parsed as integers. Letters are parsed as strings.
        The empty coalition is written as "{}".
        """
        if not isinstance(value, str):
            raise TypeError("value must be a string")

        tokens = _tokenize_power_relation_string(value)
        equivalence_classes = _parse_power_relation_tokens(tokens)

        return cls.from_nested(equivalence_classes)

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError(f"cannot set attribute '{name}' on frozen PowerRelation")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"cannot delete attribute '{name}' on frozen PowerRelation")

    @property
    def elements(self) -> tuple[Element, ...]:
        """Unique elements appearing in the relation."""
        explicit = object.__getattribute__(self, '_explicit_elements')
        if explicit is not None:
            return explicit
        elements = { element
            for equivalence_class in self.equivalence_classes
            for coalition in equivalence_class
            for element in coalition
        }
        return tuple(sorted(elements, key=_element_sort_key))

    @property
    def coalitions(self) -> tuple[Coalition, ...]:
        """All coalitions appearing in the relation."""
        return tuple(
            coalition
            for equivalence_class in self.equivalence_classes
            for coalition in equivalence_class
        )

#this is used to match R library    
    @property
    def eqs(self) -> tuple[EquivalenceClass, ...]:
        """Alias matching the R object's `eqs` field."""
        return self.equivalence_classes

    def coalition_lookup(self, coalition: CoalitionInput) -> LookupIndex:
        """Return the rank index of a coalition, or None if it is missing.
        Indexes are zero-based, so 0 is the best equivalence class.
        """
        exact_match = self._find_coalition_index(_coerce_coalition(coalition))
        if exact_match is not None:
            return exact_match
        if isinstance(coalition, str):
            return self._compact_lookup_fallback(coalition)
        return None

    def coalition_position(self, coalition: CoalitionInput) -> ElementLocation | None:
        """Return the exact position of a coalition as `(rank_index, coalition_index)`."""
        exact_match = self._find_coalition_position(_coerce_coalition(coalition))
        if exact_match is not None:
            return exact_match
        if isinstance(coalition, str):
            compact_coalition = self._parse_compact_lookup(coalition)
            if compact_coalition is not None:
                return self._find_coalition_position(compact_coalition)
        return None

    def element_lookup(self, element: Element) -> tuple[ElementLocation, ...]:
        """Return locations of coalitions containing `element`."""
        return tuple(
            (equivalence_class_index, coalition_index)
            for equivalence_class_index, equivalence_class in enumerate(self.equivalence_classes)
            for coalition_index, coalition in enumerate(equivalence_class)
            if element in coalition
        )

    def compare(self, first: CoalitionInput, second: CoalitionInput) -> int:
        """Compare two coalitions.
        Returns:
            1 if first is strictly better than second
            0 if they are indifferent
            -1 if first is strictly worse than second
        """
        first_index = self.coalition_lookup(first)
        second_index = self.coalition_lookup(second)

        if first_index is None or second_index is None:
            raise ValueError("both coalitions must appear in the power relation")
        if first_index < second_index:
            return 1
        if first_index > second_index:
            return -1
        return 0

    def strictly_prefers(self, first: CoalitionInput, second: CoalitionInput) -> bool:
        """Return whether `first` is strictly preferred to `second`."""
        return self.compare(first, second) == 1

    def weakly_prefers(self, first: CoalitionInput, second: CoalitionInput) -> bool:
        """Return whether `first` is at least as good as `second`."""
        return self.compare(first, second) >= 0

    def coalitions_are_indifferent(self, first: CoalitionInput, second: CoalitionInput) -> bool:
        """Return whether two existing coalitions are in the same equivalence class."""
        first_index = self.coalition_lookup(first)
        second_index = self.coalition_lookup(second)

        if first_index is None or second_index is None:
            return False

        return first_index == second_index

    def _find_coalition_index(self, coalition: Coalition) -> LookupIndex:
        for index, equivalence_class in enumerate(self.equivalence_classes):
            if coalition in equivalence_class:
                return index
        return None

    def _find_coalition_position(self, coalition: Coalition) -> ElementLocation | None:
        for equivalence_class_index, equivalence_class in enumerate(self.equivalence_classes):
            for coalition_index, candidate in enumerate(equivalence_class):
                if candidate == coalition:
                    return (equivalence_class_index, coalition_index)
        return None

    def _compact_lookup_fallback(self, value: str) -> LookupIndex:
        compact_coalition = self._parse_compact_lookup(value)
        if compact_coalition is None:
            return None
        return self._find_coalition_index(compact_coalition)

    def _parse_compact_lookup(self, value: str) -> Coalition | None:
        cleaned = "".join(character for character in value if not character.isspace())

        if cleaned == "{}":
            return ()

        if not cleaned or not all(character.isalnum() for character in cleaned):
            return None

        coalition = tuple(_parse_compact_element(character) for character in cleaned)

        if not all(_contains_exact_element(self.elements, element) for element in coalition):
            return None

        try:
            return _coerce_coalition(coalition)
        except (TypeError, ValueError):
            return None

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
        return hash(tuple(frozenset(equivalence_class) for equivalence_class in self.equivalence_classes))

    def __str__(self) -> str:
        compact = self._uses_compact_format()
        formatted_classes: list[str] = []

        for equivalence_class in self.equivalence_classes:
            formatted_coalitions = [_format_coalition(coalition, compact) for coalition in equivalence_class]

            if len(formatted_coalitions) == 1:
                formatted_classes.append(formatted_coalitions[0])
            else:
                formatted_classes.append(f"({' ~ '.join(formatted_coalitions)})")

        return " > ".join(formatted_classes)

    def _uses_compact_format(self) -> bool:
        element_texts = [str(element) for element in self.elements]

        if len(element_texts) != len(set(element_texts)):
            return False

        for element, text in zip(self.elements, element_texts, strict=True):
            if len(text) != 1 or not text.isalnum():
                return False

            parsed = _parse_compact_element(text)
            if type(parsed) is not type(element) or parsed != element:
                return False

        return True


def _normalize_equivalence_classes(equivalence_classes: Iterable[Iterable[CoalitionInput]]) -> tuple[EquivalenceClass, ...]:
    normalized: list[EquivalenceClass] = []
    seen_coalitions: set[Coalition] = set()

    for equivalence_class_index, equivalence_class in enumerate(equivalence_classes):
        normalized_class = tuple(_coerce_coalition(coalition) for coalition in equivalence_class)

        if not normalized_class:
            raise ValueError(f"equivalence class at index {equivalence_class_index} must not be empty")

        for coalition in normalized_class:
            if coalition in seen_coalitions:
                raise ValueError(f"duplicate coalition found: {coalition}")
            seen_coalitions.add(coalition)

        normalized.append(normalized_class)

    if not normalized:
        raise ValueError("must supply at least one equivalence class")

    return tuple(normalized)


def _coerce_coalition(coalition: CoalitionInput) -> Coalition:
    if isinstance(coalition, (list, tuple)):
        raw_coalition = tuple(coalition)
    else:
        raw_coalition = (coalition,)

    try:
        unique_elements = set(raw_coalition)
    except TypeError as error:
        raise TypeError("coalition elements must be hashable") from error

    if len(raw_coalition) != len(unique_elements):
        raise ValueError("coalition must not contain duplicate elements")

    return tuple(sorted(raw_coalition, key=_element_sort_key))


def _element_sort_key(element: Element) -> tuple[str, str, str]:
    element_type = type(element)
    return (element_type.__module__, element_type.__qualname__, repr(element))


def _contains_exact_element(elements: Iterable[Element], target: Element) -> bool:
    return any(type(element) is type(target) and element == target for element in elements)


def _format_coalition(coalition: Coalition, compact: bool) -> str:
    if not coalition:
        return "{}"

    if compact:
        return "".join(str(element) for element in coalition)

    return "{" + ", ".join(repr(element) for element in coalition) + "}"


def _tokenize_power_relation_string(value: str) -> list[str]:
    cleaned = "".join(character for character in value if not character.isspace())

    if not cleaned:
        raise ValueError("power relation string must not be empty")

    tokens: list[str] = []
    index = 0
    paren_depth = 0

    while index < len(cleaned):
        character = cleaned[index]

        if cleaned.startswith("{}", index):
            tokens.append("{}")
            index += 2
        elif character == "(":
            paren_depth += 1
            tokens.append(character)
            index += 1
        elif character == ")":
            paren_depth -= 1
            tokens.append(character)
            index += 1
        elif character in {">", "~"}:
            tokens.append(character)
            index += 1
        elif character == "'":
            # Supports tuple-like elements, e.g. ('x',) in the string.
            start = index
            index += 1
            while index < len(cleaned) and cleaned[index] != "'":
                index += 1
            if index >= len(cleaned):
                raise ValueError("unterminated quoted literal")
            index += 1  # consume closing quote
            tokens.append(cleaned[start:index])
        elif character == ",":
            # Commas are only allowed inside parentheses (tuple-like coalitions)
            if paren_depth > 0:
                index += 1
            else:
                raise ValueError("unsupported character in power relation string: ,")
        elif character.isalnum():
            start = index
            while index < len(cleaned) and cleaned[index].isalnum():
                index += 1
            tokens.append(cleaned[start:index])
        else:
            raise ValueError(f"unsupported character in power relation string: {character!r}")

    return tokens


def _parse_power_relation_tokens(tokens: list[str]) -> list[list[list[Element]]]:
    equivalence_classes: list[list[list[Element]]] = []
    index = 0

    while index < len(tokens):
        equivalence_class: list[list[Element]] = []

        if tokens[index] == "(":
            index += 1

            if index >= len(tokens) or tokens[index] in {")", ">", "~"}:
                raise ValueError("empty or malformed equivalence class")

            while True:
                coalition, index = _parse_one_coalition(tokens, index)
                equivalence_class.append(coalition)

                if index >= len(tokens):
                    raise ValueError("missing closing parenthesis")
                if tokens[index] == "~":
                    index += 1
                    if index >= len(tokens) or tokens[index] in {")", ">", "~"}:
                        raise ValueError("missing coalition after '~'")
                    continue
                if tokens[index] == ")":
                    index += 1
                    break
                raise ValueError("expected '~' or ')' inside equivalence class")
        else:
            if tokens[index] in {")", ">", "~"}:
                raise ValueError("expected coalition")
            coalition, index = _parse_one_coalition(tokens, index)
            equivalence_class.append(coalition)

        equivalence_classes.append(equivalence_class)

        if index == len(tokens):
            break
        if tokens[index] != ">":
            raise ValueError("expected '>' between equivalence classes")
        index += 1
        if index == len(tokens):
            raise ValueError("missing equivalence class after '>'")

    return equivalence_classes


def _parse_one_coalition(tokens: list[str], index: int) -> tuple[list[Element], int]:
    """Parse a single coalition starting at *index*.

    A coalition is either:
    - A simple alphanumeric token like ``"ab"`` -> elements ``['a', 'b']``
    - The empty coalition ``"{}"`` -> ``[]``
    - A **tuple-literal coalition** starting with ``(`` and ending with ``)``,
      containing quoted elements like ``'x'``.  E.g. ``('x',)`` becomes a
      coalition containing one element: the Python tuple ``('x',)``.
    """
    token = tokens[index]

    if token == "(":
        # Tuple-literal coalition: ('x',) or ('x','y') etc.
        index += 1
        tuple_elements: list[Element] = []
        while index < len(tokens) and tokens[index] != ")":
            t = tokens[index]
            if t.startswith("'") and t.endswith("'"):
                tuple_elements.append(t[1:-1])  # strip quotes
            elif t.isalnum():
                tuple_elements.append(_parse_compact_element(t) if len(t) == 1 else t)
            # skip commas and other separators
            index += 1
        if index >= len(tokens):
            raise ValueError("missing closing parenthesis for tuple literal")
        index += 1  # consume closing ')'
        # The coalition is a single element which is a tuple of the parsed items.
        return [tuple(tuple_elements)], index
    else:
        return _parse_coalition_token(token), index + 1


def _parse_coalition_token(token: str) -> list[Element]:
    if token == "{}":
        return []

    if "{" in token or "}" in token:
        raise ValueError("only the empty coalition '{}' may use braces")

    if token.startswith("'") and token.endswith("'"):
        # Single quoted literal as a standalone coalition element.
        return [token[1:-1]]

    return [_parse_compact_element(character) for character in token]


def _parse_compact_element(character: str) -> Element:
    if character.isdigit():
        return int(character)
    return character

