from socialranking.helpers import create_powerset


def test_create_powerset_orders_coalitions_largest_to_smallest():
    assert create_powerset([1, 2]) == [(1, 2), (1,), (2,), ()]


def test_create_powerset_can_exclude_empty_set():
    assert create_powerset(["a", "b"], include_empty_set=False) == [
        ("a", "b"),
        ("a",),
        ("b",),
    ]
