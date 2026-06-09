# tests/test_lexcel_extra.py
import pytest
from hypothesis import given, strategies as st

from socialranking.power_relation import PowerRelation
from socialranking.rankings import lexcel_scores, lexcel_ranking
from socialranking.social_ranking import SocialRanking


def test_lexcel_scores_single_element():
    pr = PowerRelation.from_string("a")
    assert lexcel_scores(pr) == {"a": (1,)}


def test_lexcel_ranking_single_element():
    pr = PowerRelation.from_string("a")
    assert lexcel_ranking(pr) == SocialRanking.from_string("a")


def test_lexcel_many_classes():
    chain = " > ".join(
        ["".join(chr(ord('a') + i) for i in range(k)) for k in range(1, 11)]
    )
    pr = PowerRelation.from_string(chain)
    scores = lexcel_scores(pr)
    for i, letter in enumerate("abcdefghij"):
        assert scores[letter] == tuple([0] * i + [1] * (10 - i))
    assert lexcel_ranking(pr) == SocialRanking.from_string(
        "a > b > c > d > e > f > g > h > i > j"
    )


def test_lexcel_tie_breaker_by_element_sort_key():
    pr = PowerRelation.from_string("12 > {}")
    assert lexcel_scores(pr) == {1: (1, 0), 2: (1, 0)}
    assert lexcel_ranking(pr) == SocialRanking.from_string("1 ~ 2")


def test_lexcel_non_comparable_elements():
    pr = PowerRelation.from_string("(a b) > (('x',) ~ ('y',))")
    scores = lexcel_scores(pr)
    assert scores == {
        "a": (1, 0),
        "b": (1, 0),
        ("x",): (0, 1),
        ("y",): (0, 1),
    }
    assert lexcel_ranking(pr) == SocialRanking.from_string(
        "(a ~ b) > (('x',) ~ ('y',))"
    )


def test_lexcel_no_equivalence_classes():
    pr = PowerRelation(elements={1, 2}, equivalence_classes=[])
    assert lexcel_scores(pr) == {1: (), 2: ()}
    assert lexcel_ranking(pr) == SocialRanking.from_string("1 ~ 2")


def test_lexcel_scores_none():
    with pytest.raises(TypeError, match="must be a PowerRelation instance"):
        lexcel_scores(None)  # type: ignore[arg-type]


#Hypothesis fuzz test
@st.composite
def power_relation_strings(draw):
    elems = draw(
        st.lists(
            st.integers(min_value=0, max_value=9)
            | st.text(min_size=1, max_size=1, alphabet="abcde"),
            min_size=1,
            max_size=5,
            unique=True,
        )
    )
    num_classes = draw(st.integers(min_value=1, max_value=4))
    class_strs = []
    for _ in range(num_classes):
        coalitions = draw(
            st.lists(
                st.lists(st.sampled_from(elems), min_size=1, max_size=len(elems), unique=True),
                min_size=1,
                max_size=3,
            )
        )
        class_strs.append(" ".join("".join(map(str, c)) for c in coalitions))
    return " > ".join(class_strs)


@given(power_relation_strings())
def test_lexcel_invariants(pr_str):
    try:
        pr = PowerRelation.from_string(pr_str)
    except ValueError:
        from hypothesis import reject
        reject()

    scores = lexcel_scores(pr)

    # every element appears exactly once in the dict
    assert set(scores) == set(pr.elements)

    # each score tuple length = number of equivalence classes
    assert all(len(t) == len(pr.equivalence_classes) for t in scores.values())

    # for every class, sum of counts = sum of lengths of all coalitions in that class
    for idx, eq_class in enumerate(pr.equivalence_classes):
        total = sum(scores[e][idx] for e in pr.elements)
        expected = sum(len(coalition) for coalition in eq_class)
        assert total == expected

    # ranking must be a total preorder of the same elements
    ranking = lexcel_ranking(pr)
    flat = [e for rank in ranking.ranks for e in rank]
    assert set(flat) == set(pr.elements)
