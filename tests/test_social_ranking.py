# tests/test_social_ranking_extended.py
import pytest
from collections import abc
from typing import Generator, Iterable

from socialranking.social_ranking import SocialRanking


# ----------------------------------------------------------------------
# Helper objects ---------------------------------------------------------
# ----------------------------------------------------------------------
class Dummy:
    """A hashable object with a custom sort key."""
    def __init__(self, value: int):
        self.value = value

    def __hash__(self) -> int:          # hashable
        return hash(self.value)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Dummy) and self.value == other.value

    def __repr__(self) -> str:
        return f"Dummy({self.value})"


def dummy_sort_key(x: Dummy) -> int:      # used indirectly by _element_sort_key
    return x.value


# ----------------------------------------------------------------------
# from_nested – iterator / generator handling
# ----------------------------------------------------------------------
def test_from_nested_accepts_generator():
    """A generator of iterables should be accepted."""
    def gen() -> Generator[Iterable[int], None, None]:
        yield [2, 1]
        yield (3,)

    ranking = SocialRanking.from_nested(gen())
    # Elements inside a rank must be sorted by the library’s sort key
    assert ranking.ranks == ((1, 2), (3,))


def test_from_nested_accepts_set_as_rank():
    """A set is an iterable; order must be sorted deterministically."""
    ranking = SocialRanking.from_nested([{3, 1, 2}])
    assert ranking.ranks == ((1, 2, 3),)
    # __str__ must use the sorted order
    assert str(ranking) == "(1 ~ 2 ~ 3)"


def test_from_nested_rejects_non_iterable_rank():
    with pytest.raises(TypeError, match="must be an iterable"):
        SocialRanking.from_nested([1])   # 1 is not iterable


def test_from_nested_deep_mixed_nesting():
    """Mixed 2‑ and 3‑level nesting should flatten exactly one level."""
    ranking = SocialRanking.from_nested([
        [[1, 2]],          # triple nesting → flatten to (1,2)
        [3, [4, 5]],       # double + inner list → (3,4,5)
        [[[6]]],           # triple → (6)
    ])
    assert ranking.ranks == (
        (1, 2),
        (3, 4, 5),
        (6,),
    )
    assert str(ranking) == "(1 ~ 2) > (3 ~ 4 ~ 5) > 6"


def test_from_nested_empty_outer_list_returns_empty_ranking():
    ranking = SocialRanking.from_nested([])
    assert ranking.ranks == ()
    assert str(ranking) == ""
    assert ranking.elements == ()


# ----------------------------------------------------------------------
# from_string – weird whitespace / characters
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "input_str,expected",
    [
        ("1>(2~3)>4", "1 > (2 ~ 3) > 4"),
        ("  1  >  2  >  3  ", "1 > 2 > 3"),
        ("a > b ~ c > d", "a > (b ~ c) > d"),
        ("-1 > (-2 ~ -3) > -4", "-1 > (-2 ~ -3) > -4"),
    ],
)
def test_from_string_various_whitespace_and_signs(input_str, expected):
    ranking = SocialRanking.from_string(input_str)
    assert str(ranking) == expected


def test_from_string_rejects_unbalanced_parentheses_multiple():
    for bad in ["(1 > 2) > 3)", "((1) > 2", "1 > (2 ~ 3", "1 > 2) > 3"]:
        with pytest.raises(ValueError, match="malformed parentheses"):
            SocialRanking.from_string(bad)


def test_from_string_rejects_duplicate_across_classes():
    with pytest.raises(ValueError, match="duplicate element found"):
        SocialRanking.from_string("1 > 2 > 1")


def test_from_string_allows_negative_and_float_like_strings():
    # The parser treats anything not pure digits as a string token
    r = SocialRanking.from_string("-1 > 2.5 > (3 ~ -4)")
    assert r.ranks == ((-1,), ("2.5",), (3, -4))
    assert str(r) == "-1 > 2.5 > (3 ~ -4)"


def test_from_string_rejects_empty_equivalence_class_without_parens():
    # "1 >  > 2" – two consecutive '>' yields an empty class
    with pytest.raises(ValueError, match="empty equivalence class"):
        SocialRanking.from_string("1 >  > 2")


# ----------------------------------------------------------------------
# elements property – caching & ordering
# ----------------------------------------------------------------------
def test_elements_property_is_cached():
    r = SocialRanking.from_string("c > b > a")
    first = r.elements
    # Force a second access; it must be the SAME OBJECT (cached)
    second = r.elements
    assert first is second
    assert first == ("a", "b", "c")


def test_elements_property_ignores_order_inside_ranks():
    r = SocialRanking.from_nested([(3, 1, 2), (4,)])
    assert r.elements == (1, 2, 3, 4)


# ----------------------------------------------------------------------
# element_lookup – edge cases
# ----------------------------------------------------------------------
def test_element_lookup_missing_returns_none():
    r = SocialRanking.from_string("1 > 2 > 3")
    assert r.element_lookup(99) is None


def test_element_lookup_is_immutable():
    r = SocialRanking.from_string("a > b")
    # the internal dict should not be mutable from the outside
    with pytest.raises(AttributeError):
        r._element_index["a"] = 42   # type: ignore[attr-defined]


# ----------------------------------------------------------------------
# compare / preference helpers – error handling
# ----------------------------------------------------------------------
def test_compare_raises_when_any_element_missing():
    r = SocialRanking.from_string("1 > 2")
    with pytest.raises(ValueError, match="both elements must appear"):
        r.compare(1, 3)


def test_compare_with_mixed_type_elements():
    r = SocialRanking.from_string("apple > banana ~ 2")
    # numeric string is considered a distinct element
    assert r.compare("banana", 2) == 0
    assert r.strictly_prefers("apple", "banana") is True
    assert r.weakly_prefers(2, "banana") is True
    assert r.elements_are_indifferent("banana", 2) is True


# ----------------------------------------------------------------------
# Equality & hashing – more corner cases
# ----------------------------------------------------------------------
def test_equality_is_order_independent_within_ranks():
    r1 = SocialRanking.from_nested([[1, 2], [3]])
    r2 = SocialRanking.from_nested([[2, 1], [3]])
    assert r1 == r2
    assert hash(r1) == hash(r2)


def test_equality_respects_number_of_ranks():
    r1 = SocialRanking.from_nested([[1], [2, 3]])
    r2 = SocialRanking.from_nested([[1, 2, 3]])
    assert r1 != r2
    assert hash(r1) != hash(r2)


def test_eq_returns_notimplemented_for_other_types():
    r = SocialRanking.from_string("1 > 2")
    assert (r == 123) is False          # falls back to NotImplemented → False
    assert (r != 123) is True


def test_hash_is_stable_across_processes():
    # Two distinct objects with identical canonical representation must hash equal
    r1 = SocialRanking.from_string("1 > (2 ~ 3) > 4")
    r2 = SocialRanking.from_nested([[1], [3, 2], [4]])
    assert hash(r1) == hash(r2)


# ----------------------------------------------------------------------
# __str__ – empty ranking & single‑element ranks
# ----------------------------------------------------------------------
def test_str_empty_ranking():
    r = SocialRanking.from_nested([])
    assert str(r) == ""


def test_str_singleton_ranks():
    r = SocialRanking.from_nested([[1], [2], [3]])
    assert str(r) == "1 > 2 > 3"


def test_str_multiple_elements_without_parentheses():
    # Should always wrap >1 element ranks in parentheses
    r = SocialRanking.from_nested([[1, 2, 3]])
    assert str(r) == "(1 ~ 2 ~ 3)"


# ----------------------------------------------------------------------
# __post_init__ – immutability guarantees
# ----------------------------------------------------------------------
def test_ranks_is_immutable_tuple():
    r = SocialRanking.from_nested([[1], [2, 3]])
    with pytest.raises(AttributeError):
        r.ranks[0] = (99,)          # type: ignore[index]


def test_cannot_modify_inner_tuple():
    r = SocialRanking.from_nested([[1], [2, 3]])
    with pytest.raises(AttributeError):
        r.ranks[1][0] = 99          # type: ignore[index]


# ----------------------------------------------------------------------
# Custom hashable objects – make sure sorting works with user‑defined __repr__
# ----------------------------------------------------------------------
def test_custom_hashable_objects_sort_correctly():
    objs = [Dummy(5), Dummy(1), Dummy(3)]
    ranking = SocialRanking.from_nested([objs])
    # Sorting should be by Dummy.value (the library’s _element_sort_key uses <)
    assert ranking.ranks == ((Dummy(1), Dummy(3), Dummy(5)),)
    # __str__ uses repr() of the objects
    assert str(ranking) == "(Dummy(1) ~ Dummy(3) ~ Dummy(5))"


# ----------------------------------------------------------------------
# from_nested – duplicate detection across mixed iterable types
# ----------------------------------------------------------------------
def test_from_nested_duplicate_across_list_and_tuple():
    with pytest.raises(ValueError, match="duplicate element found"):
        SocialRanking.from_nested([
            [1, 2],
            (2, 3),        # 2 appears in both ranks
        ])


# ----------------------------------------------------------------------
# from_nested – unhashable element deep inside nested structures
# ----------------------------------------------------------------------
def test_from_nested_unhashable_deep():
    # A dict is unhashable and is NOT a list/tuple/set, so _flatten_all treats it
    # as a leaf element. It ends up inside a rank, and __post_init__ raises TypeError.
    with pytest.raises(TypeError, match="elements must be hashable"):
        SocialRanking.from_nested([[{1: 2}]])


# ----------------------------------------------------------------------
# from_string – handling of extra parentheses that are not surrounding a class
# ----------------------------------------------------------------------
def test_from_string_extra_parentheses_not_allowed():
    # "(1) > 2" should be treated as malformed because a rank that is a
    # single element must not be wrapped in parentheses.
    with pytest.raises(ValueError, match="malformed parentheses"):
        SocialRanking.from_string("(1) > 2")


# ----------------------------------------------------------------------
# from_string – large number of equivalence classes
# ----------------------------------------------------------------------
def test_from_string_many_classes():
    # 10 ranks, each with a single integer
    expr = " > ".join(str(i) for i in range(10))
    r = SocialRanking.from_string(expr)
    assert len(r.ranks) == 10
    assert r.ranks[0] == (0,)
    assert r.ranks[-1] == (9,)
    # Ensure elements property reflects the full set
    assert r.elements == tuple(range(10))


# ----------------------------------------------------------------------
# from_string – whitespace inside parentheses with no tildes
# ----------------------------------------------------------------------
def test_from_string_parentheses_without_tilde():
    # "(5)" is illegal – parentheses must denote an equivalence class with >1 element
    with pytest.raises(ValueError, match="malformed parentheses"):
        SocialRanking.from_string("1 > (5) > 2")


# ----------------------------------------------------------------------
# from_nested – empty inner rank detection (already covered, but double‑check)
# ----------------------------------------------------------------------
def test_from_nested_empty_inner_rank_raises():
    with pytest.raises(ValueError, match="must not be empty"):
        SocialRanking.from_nested([[1], []])


# ----------------------------------------------------------------------
# from_nested – handling of generator that yields no items (empty ranking)
# ----------------------------------------------------------------------
def test_from_nested_generator_empty():
    def empty_gen():
        if False:
            yield [1]

    r = SocialRanking.from_nested(empty_gen())
    assert r.ranks == ()
    assert str(r) == ""


# ----------------------------------------------------------------------
# from_nested – ensures ranks are stored as tuples, not lists
# ----------------------------------------------------------------------
def test_from_nested_result_is_tuple_of_tuples():
    r = SocialRanking.from_nested([[1], [2, 3]])
    assert isinstance(r.ranks, tuple)
    assert all(isinstance(rank, tuple) for rank in r.ranks)


# ----------------------------------------------------------------------
# from_string – duplicate detection inside a single class
# ----------------------------------------------------------------------
def test_from_string_duplicate_inside_class():
    with pytest.raises(ValueError, match="duplicate element found"):
        SocialRanking.from_string("1 > (2 ~ 2) > 3")


# ----------------------------------------------------------------------
# from_string – rejecting stray characters (e.g., commas)
# ----------------------------------------------------------------------
def test_from_string_rejects_comma_character():
    with pytest.raises(ValueError, match="invalid character"):
        SocialRanking.from_string("1, > 2")


# ----------------------------------------------------------------------
# from_string – leading/trailing parentheses with spaces
# ----------------------------------------------------------------------
def test_from_string_parentheses_spaces():
    # Spaces inside the outer parentheses are allowed as long as they
    # surround a proper equivalence class.
    r = SocialRanking.from_string("1 > ( 2 ~   3 ) > 4")
    assert r.ranks == ((1,), (2, 3), (4,))
    assert str(r) == "1 > (2 ~ 3) > 4"


# ----------------------------------------------------------------------
# from_string – numeric strings that contain letters should be treated as strings
# ----------------------------------------------------------------------
def test_from_string_numeric_like_strings():
    r = SocialRanking.from_string("12a > 34b")
    assert r.ranks == (("12a",), ("34b",))
    assert r.elements == ("12a", "34b")


# ----------------------------------------------------------------------
# element_lookup – ensure it works for custom hashable objects
# ----------------------------------------------------------------------
def test_element_lookup_custom_hashable():
    obj_a = Dummy(10)
    obj_b = Dummy(20)
    r = SocialRanking.from_nested([[obj_a, obj_b]])
    assert r.element_lookup(obj_a) == 0
    assert r.element_lookup(obj_b) == 0
    assert r.element_lookup(Dummy(99)) is None


# ----------------------------------------------------------------------
# compare – returns correct sign for mixed int/str elements
# ----------------------------------------------------------------------
def test_compare_mixed_int_str():
    r = SocialRanking.from_string("1 > a > 2")
    # rank indices: 0 -> 1, 1 -> a, 2 -> 2
    assert r.compare(1, "a") == 1
    assert r.compare("a", 2) == 1
    assert r.compare(1, 2) == 1
    # reverse direction
    assert r.compare(2, "a") == -1


# ----------------------------------------------------------------------
# __str__ – ensure no trailing spaces or extra separators
# ----------------------------------------------------------------------
def test_str_no_trailing_spaces():
    r = SocialRanking.from_nested([[1], [2, 3], [4]])
    s = str(r)
    assert s == "1 > (2 ~ 3) > 4"
    assert s.strip() == s          # no leading/trailing whitespace
    assert " >  " not in s          # double spaces around '>' are absent


# ----------------------------------------------------------------------
# __hash__ – ensure hash does not change after accessing cached properties
# ----------------------------------------------------------------------
def test_hash_stable_after_property_access():
    r = SocialRanking.from_string("3 > 2 > 1")
    h1 = hash(r)
    # Access some cached properties
    _ = r.elements
    _ = r.ranks
    h2 = hash(r)
    assert h1 == h2
