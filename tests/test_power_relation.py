import pytest

from socialranking.power_relation import PowerRelation


# ============================================================
# from_nested tests
# ============================================================

def test_from_nested_simple_strict_relation():
    relation = PowerRelation.from_nested([
        [[1, 2]],
        [[1]],
        [[2]],
    ])

    assert str(relation) == "12 > 1 > 2"
    assert relation.equivalence_classes == (
        ((1, 2),),
        ((1,),),
        ((2,),),
    )


def test_from_nested_with_indifference():
    relation = PowerRelation.from_nested([
        [[1, 2]],
        [[1], [2]],
        [[]],
    ])

    assert str(relation) == "12 > (1 ~ 2) > {}"
    assert relation.equivalence_classes == (
        ((1, 2),),
        ((1,), (2,)),
        ((),),
    )


def test_from_nested_empty_coalition_only():
    relation = PowerRelation.from_nested([
        [[]],
    ])

    assert str(relation) == "{}"
    assert relation.elements == ()
    assert relation.coalitions == ((),)


def test_from_nested_sorts_elements_inside_coalition():
    relation = PowerRelation.from_nested([
        [[2, 1]],
    ])

    assert relation.equivalence_classes == (
        ((1, 2),),
    )
    assert str(relation) == "12"


def test_from_nested_preserves_equivalence_class_order():
    relation = PowerRelation.from_nested([
        [[3]],
        [[2]],
        [[1]],
    ])

    assert relation.coalition_lookup([3]) == 0
    assert relation.coalition_lookup([2]) == 1
    assert relation.coalition_lookup([1]) == 2


def test_from_nested_preserves_tied_coalitions_inside_class():
    relation = PowerRelation.from_nested([
        [[1], [2], [3]],
    ])

    assert relation.equivalence_classes == (
        ((1,), (2,), (3,)),
    )


def test_from_nested_accepts_string_elements():
    relation = PowerRelation.from_nested([
        [["a", "b"]],
        [["a"]],
        [["b"]],
    ])

    assert relation.elements == ("a", "b")
    assert str(relation) == "ab > a > b"


def test_from_nested_accepts_mixed_hashable_elements():
    relation = PowerRelation.from_nested([
        [[1, "a"]],
        [[1]],
        [["a"]],
    ])

    assert relation.elements == (1, "a")
    assert relation.coalition_lookup([1, "a"]) == 0


def test_from_nested_rejects_no_equivalence_classes():
    with pytest.raises(ValueError, match="must supply at least one equivalence class"):
        PowerRelation.from_nested([])


def test_from_nested_rejects_empty_equivalence_class():
    with pytest.raises(ValueError, match="must not be empty"):
        PowerRelation.from_nested([
            [[1]],
            [],
        ])


def test_from_nested_rejects_duplicate_coalition_same_class():
    with pytest.raises(ValueError, match="duplicate coalition found"):
        PowerRelation.from_nested([
            [[1], [1]],
        ])


def test_from_nested_rejects_duplicate_coalition_different_classes():
    with pytest.raises(ValueError, match="duplicate coalition found"):
        PowerRelation.from_nested([
            [[1]],
            [[1]],
        ])


def test_from_nested_rejects_duplicate_coalition_even_if_order_differs():
    with pytest.raises(ValueError, match="duplicate coalition found"):
        PowerRelation.from_nested([
            [[1, 2]],
            [[2, 1]],
        ])


def test_from_nested_rejects_duplicate_elements_inside_coalition():
    with pytest.raises(ValueError, match="coalition must not contain duplicate elements"):
        PowerRelation.from_nested([
            [[1, 1]],
        ])


def test_from_nested_rejects_unhashable_elements_inside_coalition():
    with pytest.raises(TypeError, match="coalition elements must be hashable"):
        PowerRelation.from_nested([
            [[[1, 2]]],
        ])


# ============================================================
# from_string tests
# ============================================================

def test_from_string_simple_strict_relation():
    relation = PowerRelation.from_string("12 > 1 > 2")

    assert str(relation) == "12 > 1 > 2"
    assert relation.equivalence_classes == (
        ((1, 2),),
        ((1,),),
        ((2,),),
    )


def test_from_string_with_indifference():
    relation = PowerRelation.from_string("12 > (1 ~ 2) > {}")

    assert str(relation) == "12 > (1 ~ 2) > {}"
    assert relation.equivalence_classes == (
        ((1, 2),),
        ((1,), (2,)),
        ((),),
    )


def test_from_string_with_parentheses():
    relation = PowerRelation.from_string("12 > (1 ~ 2) > {}")

    assert str(relation) == "12 > (1 ~ 2) > {}"


def test_from_string_with_no_spaces():
    relation = PowerRelation.from_string("12>(1~2)>{}")

    assert str(relation) == "12 > (1 ~ 2) > {}"


def test_from_string_with_many_spaces():
    relation = PowerRelation.from_string("  12   >   (  1   ~   2  )   >   {}  ")

    assert str(relation) == "12 > (1 ~ 2) > {}"


def test_from_string_empty_coalition_only():
    relation = PowerRelation.from_string("{}")

    assert str(relation) == "{}"
    assert relation.elements == ()
    assert relation.coalitions == ((),)


def test_from_string_letters():
    relation = PowerRelation.from_string("ab > a > b")

    assert str(relation) == "ab > a > b"
    assert relation.elements == ("a", "b")


def test_from_string_mixed_letters_and_digits():
    relation = PowerRelation.from_string("a1 > a > 1")

    assert relation.coalition_lookup(["a", 1]) == 0
    assert relation.coalition_lookup(["a"]) == 1
    assert relation.coalition_lookup([1]) == 2


def test_from_string_multidigit_is_read_as_separate_digits():
    relation = PowerRelation.from_string("10 > 1 > 0")

    assert relation.coalition_lookup([1, 0]) == 0
    assert relation.coalition_lookup([1]) == 1
    assert relation.coalition_lookup([0]) == 2


def test_from_string_sorts_digits_inside_coalition():
    relation = PowerRelation.from_string("21 > 1 > 2")

    assert str(relation) == "12 > 1 > 2"
    assert relation.coalition_lookup([1, 2]) == 0


def test_from_string_rejects_non_string_input():
    with pytest.raises(TypeError, match="value must be a string"):
        PowerRelation.from_string(123)  # type: ignore[arg-type]


def test_from_string_rejects_empty_string():
    with pytest.raises(ValueError, match="must not be empty"):
        PowerRelation.from_string("")


def test_from_string_rejects_spaces_only():
    with pytest.raises(ValueError, match="must not be empty"):
        PowerRelation.from_string("     ")


def test_from_string_rejects_starting_with_greater_than():
    with pytest.raises(ValueError, match="expected coalition|missing equivalence class|missing coalition|expected .*>.* between equivalence classes"):
        PowerRelation.from_string("> 12")


def test_from_string_rejects_ending_with_greater_than():
    with pytest.raises(ValueError, match="expected coalition|missing equivalence class|missing coalition|expected .*>.* between equivalence classes"):
        PowerRelation.from_string("12 >")


def test_from_string_rejects_starting_with_tilde():
    with pytest.raises(ValueError, match="expected coalition|missing equivalence class|missing coalition|expected .*>.* between equivalence classes"):
        PowerRelation.from_string("~ 12")


def test_from_string_rejects_ending_with_tilde():
    with pytest.raises(ValueError, match="expected coalition|missing equivalence class|missing coalition|expected .*>.* between equivalence classes"):
        PowerRelation.from_string("12 ~")


def test_from_string_rejects_double_greater_than():
    with pytest.raises(ValueError, match="expected coalition|missing equivalence class|missing coalition|expected .*>.* between equivalence classes"):
        PowerRelation.from_string("12 >> 1")


def test_from_string_rejects_double_tilde():
    with pytest.raises(ValueError, match="expected coalition|missing equivalence class|missing coalition|expected .*>.* between equivalence classes"):
        PowerRelation.from_string("1 ~~ 2")


def test_from_string_rejects_greater_than_then_tilde():
    with pytest.raises(ValueError, match="expected coalition|missing equivalence class|missing coalition|expected .*>.* between equivalence classes"):
        PowerRelation.from_string("12 > ~ 1")


def test_from_string_rejects_tilde_then_greater_than():
    with pytest.raises(ValueError, match="expected coalition|missing equivalence class|missing coalition|expected .*>.* between equivalence classes"):
        PowerRelation.from_string("12 ~ > 1")


def test_from_string_rejects_invalid_character():
    with pytest.raises(ValueError, match="unsupported character"):
        PowerRelation.from_string("12 @ 1")


def test_from_string_rejects_comma_character():
    with pytest.raises(ValueError, match="unsupported character"):
        PowerRelation.from_string("1,2 > 1")


def test_from_string_rejects_duplicate_element_inside_coalition():
    with pytest.raises(ValueError, match="coalition must not contain duplicate elements"):
        PowerRelation.from_string("11 > 1")


def test_from_string_rejects_duplicate_coalition():
    with pytest.raises(ValueError, match="duplicate coalition found"):
        PowerRelation.from_string("1 > 1")


def test_from_string_rejects_duplicate_coalition_inside_tie():
    with pytest.raises(ValueError, match="duplicate coalition found"):
        PowerRelation.from_string("(1 ~ 1)")


def test_from_string_rejects_duplicate_empty_coalition():
    with pytest.raises(ValueError, match="duplicate coalition found"):
        PowerRelation.from_string("{} > {}")


def test_from_string_rejects_missing_separator_between_coalitions():
    with pytest.raises(ValueError, match="expected '>' between equivalence classes"):
        PowerRelation.from_string("1{}")


def test_from_string_whitespace_inside_coalition_is_ignored():
    relation = PowerRelation.from_string("1 2")

    assert relation.equivalence_classes == (((1, 2),),)


def test_from_string_rejects_empty_parentheses():
    with pytest.raises(ValueError, match="empty or malformed equivalence class"):
        PowerRelation.from_string("()")


def test_from_string_rejects_missing_coalition_after_tilde_in_parentheses():
    with pytest.raises(ValueError, match="missing coalition after '~'"):
        PowerRelation.from_string("(1 ~)")


def test_from_string_rejects_missing_closing_parenthesis():
    with pytest.raises(ValueError, match="missing closing parenthesis"):
        PowerRelation.from_string("(1 ~ 2")


def test_from_string_rejects_greater_than_inside_parentheses():
    with pytest.raises(ValueError, match="inside equivalence class"):
        PowerRelation.from_string("(1 > 2)")


def test_from_string_rejects_non_empty_braced_coalition():
    with pytest.raises(ValueError, match="unsupported character"):
        PowerRelation.from_string("{1}")


def test_from_string_accepts_parenthesized_single_coalition():
    relation = PowerRelation.from_string("(12)")

    assert relation.equivalence_classes == (((1, 2),),)


# ============================================================
# elements property tests
# ============================================================

def test_elements_returns_unique_elements():
    relation = PowerRelation.from_nested([
        [[1, 2]],
        [[1]],
        [[2]],
    ])

    assert relation.elements == (1, 2)


def test_elements_ignores_empty_coalition():
    relation = PowerRelation.from_nested([
        [[1]],
        [[]],
    ])

    assert relation.elements == (1,)


def test_elements_returns_sorted_numbers():
    relation = PowerRelation.from_nested([
        [[3, 1, 2]],
    ])

    assert relation.elements == (1, 2, 3)


def test_elements_returns_sorted_strings():
    relation = PowerRelation.from_nested([
        [["c", "a", "b"]],
    ])

    assert relation.elements == ("a", "b", "c")


def test_elements_stable_for_mixed_types():
    relation = PowerRelation.from_nested([
        [[2, "a", 1]],
    ])

    assert relation.elements == (1, 2, "a")


# ============================================================
# coalitions property tests
# ============================================================

def test_coalitions_returns_all_coalitions_in_order():
    relation = PowerRelation.from_string("12 > (1 ~ 2) > {}")

    assert relation.coalitions == ((1, 2), (1,), (2,), ())


def test_coalitions_with_single_class():
    relation = PowerRelation.from_string("(1 ~ 2 ~ 3)")

    assert relation.coalitions == ((1,), (2,), (3,))


def test_coalitions_with_empty_coalition():
    relation = PowerRelation.from_string("{}")

    assert relation.coalitions == ((),)


# ============================================================
# coalition_lookup tests
# ============================================================

def test_coalition_lookup_existing_pair():
    relation = PowerRelation.from_string("12 > 1 > 2")

    assert relation.coalition_lookup([1, 2]) == 0


def test_coalition_lookup_existing_singleton_as_list():
    relation = PowerRelation.from_string("12 > 1 > 2")

    assert relation.coalition_lookup([1]) == 1


def test_coalition_lookup_existing_singleton_as_tuple():
    relation = PowerRelation.from_string("12 > 1 > 2")

    assert relation.coalition_lookup((1,)) == 1


def test_coalition_lookup_existing_singleton_as_element():
    relation = PowerRelation.from_string("12 > 1 > 2")

    assert relation.coalition_lookup(1) == 1


def test_coalition_lookup_empty_coalition():
    relation = PowerRelation.from_string("12 > 1 > {}")

    assert relation.coalition_lookup([]) == 2
    assert relation.coalition_lookup(()) == 2


def test_coalition_lookup_order_independent():
    relation = PowerRelation.from_string("12 > 1 > 2")

    assert relation.coalition_lookup([2, 1]) == 0


def test_coalition_lookup_compact_string_pair():
    relation = PowerRelation.from_string("12 > 1 > 2")

    assert relation.coalition_lookup("12") == 0


def test_coalition_lookup_compact_string_strips_whitespace():
    relation = PowerRelation.from_string("12 > 1 > 2")

    assert relation.coalition_lookup(" 1 2 ") == 0


def test_coalition_lookup_compact_empty_coalition_string():
    relation = PowerRelation.from_string("12 > 1 > {}")

    assert relation.coalition_lookup("{}") == 2


def test_coalition_lookup_compact_string_missing_element_returns_none():
    relation = PowerRelation.from_string("12 > 1 > 2")

    assert relation.coalition_lookup("13") is None


def test_coalition_lookup_non_alphanumeric_string_returns_none():
    relation = PowerRelation.from_string("12 > 1 > 2")

    assert relation.coalition_lookup("1-2") is None


def test_coalition_lookup_missing_returns_none():
    relation = PowerRelation.from_string("12 > 1 > {}")

    assert relation.coalition_lookup([2]) is None


def test_coalition_lookup_rejects_duplicate_elements():
    relation = PowerRelation.from_string("12 > 1 > 2")

    with pytest.raises(ValueError, match="coalition must not contain duplicate elements"):
        relation.coalition_lookup([1, 1])


def test_coalition_lookup_rejects_unhashable_element():
    relation = PowerRelation.from_string("12 > 1 > 2")

    with pytest.raises(TypeError, match="coalition elements must be hashable"):
        relation.coalition_lookup([[1]])


# ============================================================
# coalition_position tests
# ============================================================

def test_coalition_position_first_class():
    relation = PowerRelation.from_string("12 > (1 ~ 2) > {}")

    assert relation.coalition_position([1, 2]) == (0, 0)


def test_coalition_position_second_class_first_coalition():
    relation = PowerRelation.from_string("12 > (1 ~ 2) > {}")

    assert relation.coalition_position([1]) == (1, 0)


def test_coalition_position_second_class_second_coalition():
    relation = PowerRelation.from_string("12 > (1 ~ 2) > {}")

    assert relation.coalition_position([2]) == (1, 1)


def test_coalition_position_empty_coalition():
    relation = PowerRelation.from_string("12 > (1 ~ 2) > {}")

    assert relation.coalition_position([]) == (2, 0)


def test_coalition_position_missing_returns_none():
    relation = PowerRelation.from_string("12 > 1 > {}")

    assert relation.coalition_position([2]) is None


def test_coalition_position_order_independent():
    relation = PowerRelation.from_string("12 > 1 > 2")

    assert relation.coalition_position([2, 1]) == (0, 0)


def test_coalition_position_compact_string_pair():
    relation = PowerRelation.from_string("12 > 1 > 2")

    assert relation.coalition_position("12") == (0, 0)


def test_coalition_position_rejects_duplicate_elements():
    relation = PowerRelation.from_string("12 > 1 > 2")

    with pytest.raises(ValueError, match="coalition must not contain duplicate elements"):
        relation.coalition_position([1, 1])


def test_coalition_position_rejects_unhashable_element():
    relation = PowerRelation.from_string("12 > 1 > 2")

    with pytest.raises(TypeError, match="coalition elements must be hashable"):
        relation.coalition_position([[1]])


# ============================================================
# element_lookup tests
# ============================================================

def test_element_lookup_single_occurrence():
    relation = PowerRelation.from_string("12 > 1 > 2")

    assert relation.element_lookup(2) == ((0, 0), (2, 0))


def test_element_lookup_multiple_occurrences():
    relation = PowerRelation.from_nested([
        [[1, 2, 3]],
        [[1, 2]],
        [[1]],
        [[]],
    ])

    assert relation.element_lookup(1) == ((0, 0), (1, 0), (2, 0))


def test_element_lookup_missing_element():
    relation = PowerRelation.from_string("12 > 1 > 2")

    assert relation.element_lookup(3) == ()


def test_element_lookup_empty_relation_elements():
    relation = PowerRelation.from_string("{}")

    assert relation.element_lookup(1) == ()


def test_element_lookup_string_element():
    relation = PowerRelation.from_string("ab > a > b")

    assert relation.element_lookup("a") == ((0, 0), (1, 0))


def test_element_lookup_uses_python_equality_for_matching():
    relation = PowerRelation.from_nested([
        [[1]],
    ])

    assert relation.element_lookup(True) == ((0, 0),)


# ============================================================
# compare tests
# ============================================================

def test_compare_first_strictly_better():
    relation = PowerRelation.from_string("12 > 1 > 2")

    assert relation.compare([1, 2], [1]) == 1


def test_compare_first_strictly_worse():
    relation = PowerRelation.from_string("12 > 1 > 2")

    assert relation.compare([2], [1]) == -1


def test_compare_indifferent():
    relation = PowerRelation.from_string("12 > (1 ~ 2) > {}")

    assert relation.compare([1], [2]) == 0


def test_compare_same_coalition():
    relation = PowerRelation.from_string("12 > 1 > 2")

    assert relation.compare([1], [1]) == 0


def test_compare_empty_coalition_worse():
    relation = PowerRelation.from_string("12 > 1 > {}")

    assert relation.compare([], [1]) == -1


def test_compare_empty_coalition_equal_to_itself():
    relation = PowerRelation.from_string("12 > 1 > {}")

    assert relation.compare([], []) == 0


def test_compare_accepts_single_element_input():
    relation = PowerRelation.from_string("12 > 1 > 2")

    assert relation.compare(1, 2) == 1


def test_compare_order_independent():
    relation = PowerRelation.from_string("12 > 1 > 2")

    assert relation.compare([2, 1], [1]) == 1


def test_compare_accepts_compact_string_input():
    relation = PowerRelation.from_string("12 > 1 > 2")

    assert relation.compare("12", "1") == 1


def test_compare_missing_first_raises_error():
    relation = PowerRelation.from_string("12 > 1 > {}")

    with pytest.raises(ValueError, match="both coalitions must appear"):
        relation.compare([2], [1])


def test_compare_missing_second_raises_error():
    relation = PowerRelation.from_string("12 > 1 > {}")

    with pytest.raises(ValueError, match="both coalitions must appear"):
        relation.compare([1], [2])


def test_compare_both_missing_raises_first_error():
    relation = PowerRelation.from_string("1 > {}")

    with pytest.raises(ValueError, match="both coalitions must appear"):
        relation.compare([2], [3])


# ============================================================
# strictly_prefers tests
# ============================================================

def test_strictly_prefers_true():
    relation = PowerRelation.from_string("12 > 1 > 2")

    assert relation.strictly_prefers([1, 2], [1]) is True


def test_strictly_prefers_false_when_worse():
    relation = PowerRelation.from_string("12 > 1 > 2")

    assert relation.strictly_prefers([2], [1]) is False


def test_strictly_prefers_false_when_equal():
    relation = PowerRelation.from_string("12 > (1 ~ 2) > {}")

    assert relation.strictly_prefers([1], [2]) is False


def test_strictly_prefers_raises_for_missing_coalition():
    relation = PowerRelation.from_string("1 > {}")

    with pytest.raises(ValueError):
        relation.strictly_prefers([2], [1])


# ============================================================
# weakly_prefers tests
# ============================================================

def test_weakly_prefers_true_when_better():
    relation = PowerRelation.from_string("12 > 1 > 2")

    assert relation.weakly_prefers([1, 2], [1]) is True


def test_weakly_prefers_true_when_equal():
    relation = PowerRelation.from_string("12 > (1 ~ 2) > {}")

    assert relation.weakly_prefers([1], [2]) is True


def test_weakly_prefers_false_when_worse():
    relation = PowerRelation.from_string("12 > 1 > 2")

    assert relation.weakly_prefers([2], [1]) is False


def test_weakly_prefers_raises_for_missing_coalition():
    relation = PowerRelation.from_string("1 > {}")

    with pytest.raises(ValueError):
        relation.weakly_prefers([2], [1])


# ============================================================
# coalitions_are_indifferent tests
# ============================================================

def test_coalitions_are_indifferent_true_for_tie():
    relation = PowerRelation.from_string("12 > (1 ~ 2) > {}")

    assert relation.coalitions_are_indifferent([1], [2]) is True


def test_coalitions_are_indifferent_true_for_same_coalition():
    relation = PowerRelation.from_string("12 > 1 > 2")

    assert relation.coalitions_are_indifferent([1], [1]) is True


def test_coalitions_are_indifferent_false_for_different_classes():
    relation = PowerRelation.from_string("12 > 1 > 2")

    assert relation.coalitions_are_indifferent([1], [2]) is False


def test_coalitions_are_indifferent_false_when_first_missing():
    relation = PowerRelation.from_string("12 > 1 > {}")

    assert relation.coalitions_are_indifferent([2], [1]) is False


def test_coalitions_are_indifferent_false_when_second_missing():
    relation = PowerRelation.from_string("12 > 1 > {}")

    assert relation.coalitions_are_indifferent([1], [2]) is False


def test_coalitions_are_indifferent_false_when_both_missing():
    relation = PowerRelation.from_string("1 > {}")

    assert relation.coalitions_are_indifferent([2], [3]) is False


# ============================================================
# equality and hashing tests
# ============================================================

def test_equal_relations_from_nested_and_string():
    first = PowerRelation.from_nested([
        [[1, 2]],
        [[1], [2]],
        [[]],
    ])
    second = PowerRelation.from_string("12 > (1 ~ 2) > {}")

    assert first == second


def test_equal_relations_ignore_order_inside_tie_for_equality():
    first = PowerRelation.from_nested([
        [[1, 2]],
        [[1], [2]],
    ])
    second = PowerRelation.from_nested([
        [[2, 1]],
        [[2], [1]],
    ])

    assert first == second


def test_not_equal_when_class_order_differs():
    first = PowerRelation.from_string("12 > 1 > 2")
    second = PowerRelation.from_string("12 > 2 > 1")

    assert first != second


def test_not_equal_when_number_of_classes_differs():
    first = PowerRelation.from_string("12 > (1 ~ 2)")
    second = PowerRelation.from_string("12 > 1 > 2")

    assert first != second


def test_not_equal_to_unrelated_object():
    relation = PowerRelation.from_string("12 > 1 > 2")

    assert relation != "12 > 1 > 2"


def test_hash_equal_for_equal_relations():
    first = PowerRelation.from_string("12 > (1 ~ 2) > {}")
    second = PowerRelation.from_nested([
        [[1, 2]],
        [[2], [1]],
        [[]],
    ])

    assert hash(first) == hash(second)


def test_hash_equal_when_tied_coalition_order_differs():
    first = PowerRelation.from_nested([
        [[1], [2]],
    ])
    second = PowerRelation.from_nested([
        [[2], [1]],
    ])

    assert first == second
    assert hash(first) == hash(second)


def test_not_equal_when_same_coalitions_have_different_class_structure():
    first = PowerRelation.from_string("12 > (1 ~ 2)")
    second = PowerRelation.from_string("(12 ~ 1) > 2")

    assert first != second


def test_relation_can_be_used_in_set():
    first = PowerRelation.from_string("12 > (1 ~ 2) > {}")
    second = PowerRelation.from_nested([
        [[1, 2]],
        [[2], [1]],
        [[]],
    ])

    relations = {first, second}

    assert len(relations) == 1


# ============================================================
# string representation tests
# ============================================================

def test_str_compact_single_digit_numbers():
    relation = PowerRelation.from_nested([
        [[1, 2]],
        [[1]],
        [[2]],
    ])

    assert str(relation) == "12 > 1 > 2"


def test_str_compact_letters():
    relation = PowerRelation.from_nested([
        [["a", "b"]],
        [["a"]],
        [["b"]],
    ])

    assert str(relation) == "ab > a > b"


def test_str_tied_class_has_parentheses():
    relation = PowerRelation.from_string("(1 ~ 2) > {}")

    assert str(relation) == "(1 ~ 2) > {}"


def test_str_singleton_class_has_no_parentheses():
    relation = PowerRelation.from_string("1 > 2 > {}")

    assert str(relation) == "1 > 2 > {}"


def test_str_noncompact_for_multi_character_element():
    relation = PowerRelation.from_nested([
        [["player1", "player2"]],
        [["player1"]],
    ])

    assert str(relation) == "{'player1', 'player2'} > {'player1'}"


def test_str_noncompact_for_number_with_two_digits():
    relation = PowerRelation.from_nested([
        [[10, 2]],
        [[10]],
    ])

    assert str(relation) == "{10, 2} > {10}"


def test_str_empty_coalition_in_noncompact_relation():
    relation = PowerRelation.from_nested([
        [["player1"]],
        [[]],
    ])

    assert str(relation) == "{'player1'} > {}"


def test_str_mixed_type_relation():
    relation = PowerRelation.from_nested([
        [[1, "a"]],
        [[1]],
        [["a"]],
    ])

    assert str(relation) == "1a > 1 > a"


def test_str_noncompact_when_string_digit_would_not_round_trip():
    relation = PowerRelation.from_nested([
        [["1"]],
    ])

    assert str(relation) == "{'1'}"


# ============================================================
# immutability tests
# ============================================================

def test_power_relation_is_frozen():
    relation = PowerRelation.from_string("12 > 1 > 2")

    with pytest.raises(Exception):
        relation.equivalence_classes = ()  # type: ignore[misc]


def test_internal_equivalence_classes_are_tuples():
    relation = PowerRelation.from_string("12 > 1 > 2")

    assert isinstance(relation.equivalence_classes, tuple)
    assert isinstance(relation.equivalence_classes[0], tuple)
    assert isinstance(relation.equivalence_classes[0][0], tuple)


# ============================================================
# direct constructor tests
# ============================================================

def test_direct_constructor_normalizes_input():
    relation = PowerRelation((
        ((2, 1),),
        ((1,),),
    ))

    assert relation.equivalence_classes == (
        ((1, 2),),
        ((1,),),
    )


def test_direct_constructor_rejects_empty_tuple():
    with pytest.raises(ValueError):
        PowerRelation(())


def test_direct_constructor_rejects_empty_class():
    with pytest.raises(ValueError):
        PowerRelation(((),))


def test_direct_constructor_rejects_duplicate_coalitions():
    with pytest.raises(ValueError):
        PowerRelation((
            ((1,),),
            ((1,),),
        ))


# ============================================================
# extra edge cases
# ============================================================

def test_single_element_as_string_is_one_element_coalition():
    relation = PowerRelation.from_nested([
        [["ab"]],
    ])

    assert relation.coalition_lookup("ab") == 0
    assert str(relation) == "{'ab'}"


def test_list_of_strings_is_coalition_of_strings():
    relation = PowerRelation.from_nested([
        [["a", "b"]],
    ])

    assert relation.coalition_lookup(["a", "b"]) == 0
    assert relation.coalition_lookup("a") is None


def test_tuple_input_to_coalition_lookup():
    relation = PowerRelation.from_string("12 > 1 > 2")

    assert relation.coalition_lookup((1, 2)) == 0


def test_empty_tuple_lookup_matches_empty_coalition():
    relation = PowerRelation.from_string("1 > {}")

    assert relation.coalition_lookup(()) == 1


def test_empty_list_lookup_matches_empty_coalition():
    relation = PowerRelation.from_string("1 > {}")

    assert relation.coalition_lookup([]) == 1


def test_large_relation_basic_operations():
    relation = PowerRelation.from_nested([
        [[1, 2, 3]],
        [[1, 2], [1, 3], [2, 3]],
        [[1], [2], [3]],
        [[]],
    ])

    assert relation.elements == (1, 2, 3)
    assert relation.coalition_lookup([1, 2, 3]) == 0
    assert relation.coalition_lookup([1, 2]) == 1
    assert relation.coalition_lookup([3]) == 2
    assert relation.coalition_lookup([]) == 3
    assert relation.strictly_prefers([1, 2, 3], [1, 2])
    assert relation.coalitions_are_indifferent([1, 2], [2, 3])
