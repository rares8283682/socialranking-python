"""Ranking solution functions.

The first implementation is lexicographical excellence (Lexcel).
"""

from __future__ import annotations
from typing import Hashable
from socialranking.power_relation import PowerRelation, _element_sort_key
from socialranking.social_ranking import SocialRanking

Element = Hashable

def lexcel_scores(power_relation: PowerRelation) -> dict[Element, tuple[int, ...]]:
    """Calculate Lexicographical Excellence (Lexcel) scores for each element.

    For every equivalence class in ``power_relation.equivalence_classes``, count how many coalitions
    in that class contain the element.  The score vector always has one entry
    per equivalence class (including zeros), so all score vectors have the
    same length.

    References:
        Bernardi, Lucchetti, Moretti (2019). "Ranking objects from a
        preference relation over their subsets."
    """
    if not isinstance(power_relation, PowerRelation):
        raise TypeError("power_relation must be a PowerRelation instance")

    # Build score vector for every element across ALL equivalence classes.
    scores: dict[Element, list[int]] = {e: [] for e in power_relation.elements}

    for eq_class in power_relation.equivalence_classes:
        for e in power_relation.elements:
            count = sum(1 for coalition in eq_class if e in coalition)
            scores[e].append(count)

    return {e: tuple(counts) for e, counts in scores.items()}


def lexcel_ranking(power_relation: PowerRelation) -> SocialRanking:
    """Rank elements using the Lexicographical Excellence (Lexcel) method.
    1. Compute Lexcel scores for each element.
    2. Sort elements by score vector in descending lexicographic order.
    3. Group elements with *identical* score vectors into the same rank.
    4. Within each rank, elements are sorted by ``_element_sort_key``
       (type module, type qualname, repr) — ascending.

    Elements with equal scores that can't be distinguished are tied
    (indifferent), matching the academic definition of Lexcel as a
    total preorder.
    """
    if not isinstance(power_relation, PowerRelation):
        raise TypeError("power_relation must be a PowerRelation instance")

    scores = lexcel_scores(power_relation)

    if not scores:
        raise ValueError("PowerRelation contains no elements")

    # Sort: primary key = score descending, secondary key = element sort key ascending.
    # Python's sort is stable, so we do a two-step sort:
    #   Step 1: sort by element key ascending (secondary / tiebreaker)
    #   Step 2: sort by score descending (primary)
    elements_list = list(scores.keys())
    elements_list.sort(key=_element_sort_key)
    elements_list.sort(key=lambda e: scores[e], reverse=True)

    # Group consecutive elements with identical scores into the same rank.
    ranks: list[list[Element]] = []
    current_rank: list[Element] = [elements_list[0]]

    for elem in elements_list[1:]:
        if scores[elem] == scores[current_rank[0]]:
            current_rank.append(elem)
        else:
            ranks.append(current_rank)
            current_rank = [elem]
    ranks.append(current_rank)

    return SocialRanking(tuple(tuple(r) for r in ranks))
