"""Core social ranking data structure."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable


Element = Hashable
Rank = tuple[Element, ...]


@dataclass(frozen=True)
class SocialRanking:
    """Ordered equivalence classes of individual elements."""

    ranks: tuple[Rank, ...]

    @classmethod
    def from_nested(cls, ranks: list[list[Element]]) -> "SocialRanking":
        """Create a social ranking from nested Python lists."""
        return cls(tuple(tuple(sorted(rank)) for rank in ranks))
