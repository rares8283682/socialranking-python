"""Ranking solution functions.

The first implementation here is lexicographical excellence (Lexcel).
"""

from __future__ import annotations

from typing import Hashable

from socialranking.power_relation import PowerRelation, _element_sort_key
from socialranking.social_ranking import SocialRanking

Element = Hashable


def lexcel_scores(power_relation: PowerRelation) -> dict[Element, tuple[int, ...]]:
    """Calculate the Lexicographical Excellence (or Lexcel) score for each element.

    The Lexcel score of an element is a tuple of integers, where the i-th entry
    indicates the number of times that element appears in the i-th equivalence
    class of the power relation.

    Returns a dictionary mapping elements to their Lexcel score tuples.
    """
    if not isinstance(power_relation, PowerRelation):
        raise TypeError("power_relation must be a PowerRelation instance")

    scores: dict[Element, tuple[int, ...]] = {}
    for element in power_relation.elements:
        score_list: list[int] = []
        for eq_class in power_relation.equivalence_classes:
            # Count the number of coalitions in this equivalence class containing the element
            count = sum(1 for coalition in eq_class if element in coalition)
            score_list.append(count)
        scores[element] = tuple(score_list)

    return scores


def lexcel_ranking(power_relation: PowerRelation) -> SocialRanking:
    """Rank elements using the Lexicographical Excellence (Lexcel) method.

    Elements are ranked according to their Lexcel score vectors compared
    lexicographically in descending order. Elements with identical scores
    are grouped into the same rank.
    """
    if not isinstance(power_relation, PowerRelation):
        raise TypeError("power_relation must be a PowerRelation instance")

    scores = lexcel_scores(power_relation)

    # Sort elements stably:
    # 1. Sort by elements' natural sort key ascending to break ties deterministically
    elements_list = list(scores.keys())
    elements_list.sort(key=_element_sort_key)

    # 2. Sort by scores descending
    elements_list.sort(key=lambda x: scores[x], reverse=True)

    # Group elements into equivalence classes (ranks)
    ranks: list[list[Element]] = []
    current_rank: list[Element] = []
    current_score = None

    for element in elements_list:
        score = scores[element]
        if current_score is None:
            current_score = score
            current_rank = [element]
        elif score == current_score:
            current_rank.append(element)
        else:
            ranks.append(current_rank)
            current_score = score
            current_rank = [element]

    if current_rank:
        ranks.append(current_rank)

    return SocialRanking.from_nested(ranks)
