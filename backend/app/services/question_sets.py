"""Picking a student's 40-question interest test set (rotation PRD T3; plan
Step 9.2 task 3, Processing Flow C).

Pure functions: no database, no clock. The caller passes the bank, the
student's past sets, and a random-number source, so tests can use a fixed
seed and get the same set every time.

Rules:
- **Size:** `SET_SIZE` different questions.
- **Balance:** every area should appear in `MIN_PER_AREA` to `MAX_PER_AREA`
  of them. Each pick takes the question whose areas are currently least
  represented, so counts stay close together. Ties go to whichever came first
  in the shuffled order, which keeps sets varied.
- **Freshness:** only unseen questions are used while at least `SET_SIZE` are
  left. Otherwise every unseen question is used, then the set is topped up
  with questions seen longest ago, never from the most recent set.
"""

import random
from collections import Counter
from collections.abc import Collection, Mapping, Sequence

SET_SIZE = 40
MIN_PER_AREA = 16
MAX_PER_AREA = 20


def is_balanced(question_ids: Sequence[int], question_areas: Mapping[int, Collection[str]]) -> bool:
    """True if every area in the bank appears in MIN..MAX of the questions."""
    all_areas = {area for areas in question_areas.values() for area in areas}
    counts = Counter(area for q in question_ids for area in question_areas[q])
    return all(MIN_PER_AREA <= counts[area] <= MAX_PER_AREA for area in all_areas)


def _shuffled(items: Collection[int], rng: random.Random) -> list[int]:
    result = sorted(items)
    rng.shuffle(result)
    return result


def _pool(
    question_areas: Mapping[int, Collection[str]], past_sets: Sequence[Sequence[int]], rng: random.Random, size: int
) -> tuple[list[int], list[int]]:
    """Return (forced, candidates): questions that must be in the set, and
    the shuffled questions the rest is picked from."""
    last_seen: dict[int, int] = {}
    for index, past in enumerate(past_sets):
        for q in past:
            last_seen[q] = index

    fresh = [q for q in question_areas if q not in last_seen]
    if len(fresh) >= size:
        return [], _shuffled(fresh, rng)

    # Not enough unseen questions: use them all, then top up from the sets
    # seen longest ago, one whole set at a time, never the most recent set.
    most_recent = len(past_sets) - 1
    candidates: list[int] = []
    for index in range(most_recent):
        tier = [q for q, seen in last_seen.items() if seen == index and q in question_areas]
        candidates.extend(_shuffled(tier, rng))
        if len(fresh) + len(candidates) >= 2 * size:
            break
    if len(fresh) + len(candidates) < size:
        # A tiny bank: the most recent set is the only place left to look.
        candidates.extend(
            _shuffled([q for q, seen in last_seen.items() if seen == most_recent and q in question_areas], rng)
        )
    return _shuffled(fresh, rng), candidates


def draw_set(
    question_areas: Mapping[int, Collection[str]],
    past_sets: Sequence[Sequence[int]],
    rng: random.Random,
    size: int = SET_SIZE,
) -> list[int]:
    """Pick a new set of question ids, in display order.

    `question_areas` maps every bank question id to its answer areas ("None
    of the above" excluded). `past_sets` lists the student's earlier sets,
    oldest first, each as its question ids.
    """
    forced, candidates = _pool(question_areas, past_sets, rng, size)

    chosen: list[int] = []
    counts: Counter[str] = Counter()
    for q in forced[:size]:
        chosen.append(q)
        counts.update(question_areas[q])

    remaining = list(candidates)
    while len(chosen) < size and remaining:
        best_index = None
        best_score = -1
        for index, q in enumerate(remaining):
            areas = question_areas[q]
            if any(counts[area] >= MAX_PER_AREA for area in areas):
                continue
            score = sum(MAX_PER_AREA - counts[area] for area in areas)
            if score > best_score:
                best_index, best_score = index, score
        if best_index is None:
            # Every candidate would push an area over the cap: take the one
            # that goes over by the least, so the set still fills up.
            best_index = min(
                range(len(remaining)), key=lambda i: max(counts[area] for area in question_areas[remaining[i]])
            )
        q = remaining.pop(best_index)
        chosen.append(q)
        counts.update(question_areas[q])

    rng.shuffle(chosen)
    return chosen
