import pytest

from socialranking.helpers import create_powerset


@pytest.mark.parametrize(
    ("elements", "expected"),
    [
        ([], [()]),
        ([1], [(1,), ()]),
        ([1, 2], [(1, 2), (1,), (2,), ()]),
        (
            [1, 2, 3],
            [
                (1, 2, 3),
                (1, 2),
                (1, 3),
                (2, 3),
                (1,),
                (2,),
                (3,),
                (),
            ],
        ),
    ],
)
def test_create_powerset_returns_expected_coalitions(elements, expected):
    assert create_powerset(elements) == expected


def test_create_powerset_can_exclude_empty_coalition():
    assert create_powerset(["a", "b"], include_empty_set=False) == [
        ("a", "b"),
        ("a",),
        ("b",),
    ]


def test_create_powerset_empty_input_without_empty_coalition():
    assert create_powerset([], include_empty_set=False) == []


def test_create_powerset_preserves_input_order_inside_same_size():
    assert create_powerset([3, 1, 2]) == [
        (3, 1, 2),
        (3, 1),
        (3, 2),
        (1, 2),
        (3,),
        (1,),
        (2,),
        (),
    ]


def test_create_powerset_returns_tuples():
    result = create_powerset([1, 2, 3])

    assert all(isinstance(coalition, tuple) for coalition in result)


def test_create_powerset_result_lengths_are_descending():
    result = create_powerset(["a", "b", "c"])

    assert [len(coalition) for coalition in result] == [3, 2, 2, 2, 1, 1, 1, 0]


@pytest.mark.parametrize(
    ("elements", "include_empty_set", "expected_length"),
    [
        ([1, 2, 3], True, 8),
        ([1, 2, 3], False, 7),
        (["a", "b", "c", "d"], True, 16),
        (["a", "b", "c", "d"], False, 15),
    ],
)
def test_create_powerset_result_length_matches_powerset_size(
    elements,
    include_empty_set,
    expected_length,
):
    assert len(create_powerset(elements, include_empty_set)) == expected_length


def test_create_powerset_accepts_generator_input():
    elements = (number for number in [1, 2, 3])

    assert create_powerset(elements) == [
        (1, 2, 3),
        (1, 2),
        (1, 3),
        (2, 3),
        (1,),
        (2,),
        (3,),
        (),
    ]


def test_create_powerset_accepts_tuple_elements_as_hashable_elements():
    assert create_powerset([(1, 2), (3, 4)]) == [
        ((1, 2), (3, 4)),
        ((1, 2),),
        ((3, 4),),
        (),
    ]


def test_create_powerset_treats_string_as_iterable_of_characters():
    assert create_powerset("abc") == [
        ("a", "b", "c"),
        ("a", "b"),
        ("a", "c"),
        ("b", "c"),
        ("a",),
        ("b",),
        ("c",),
        (),
    ]


@pytest.mark.parametrize(
    "elements",
    [
        [1, 1],
        ["a", "b", "a"],
        [(1, 2), (1, 2)],
        [1, True],
    ],
)
def test_create_powerset_rejects_duplicate_elements(elements):
    with pytest.raises(ValueError, match="elements must not contain duplicates"):
        create_powerset(elements)


@pytest.mark.parametrize(
    "elements",
    [
        [[1], [2]],
        [{"a": 1}, {"b": 2}],
        [{1}, {2}],
    ],
)
def test_create_powerset_rejects_non_hashable_elements(elements):
    with pytest.raises(TypeError, match="elements must be hashable"):
        create_powerset(elements)
