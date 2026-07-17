"""Shared 0-100 normalization (CLAUDE.md Sec 7 preamble): every sub-score is
normalized within its own population before being combined, so weights in
the composite are comparable. Percentile rank, not min-max -- robust to the
extreme outliers that "amount disclosed as a range, sold 50000 shares" type
trades produce (a min-max scale would let one whale trade compress
everything else toward 0).
"""

from __future__ import annotations


def percentile_rank(values: dict[int, float]) -> dict[int, float]:
    """key -> raw value, returns key -> percentile rank in [0, 100].
    Ties share the same rank (average position among tied values).
    """
    if not values:
        return {}
    if len(values) == 1:
        key = next(iter(values))
        return {key: 100.0}

    sorted_items = sorted(values.items(), key=lambda kv: kv[1])
    n = len(sorted_items)
    ranks: dict[int, float] = {}

    i = 0
    while i < n:
        j = i
        while j + 1 < n and sorted_items[j + 1][1] == sorted_items[i][1]:
            j += 1
        avg_position = (i + j) / 2
        percentile = 100.0 * avg_position / (n - 1)
        for k in range(i, j + 1):
            ranks[sorted_items[k][0]] = percentile
        i = j + 1

    return ranks
