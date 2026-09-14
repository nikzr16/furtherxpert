"""Unit tests for `app/services/question_sets.py` (rotation PRD T3, criteria
3-4; rotation plan Testing Strategy "Set drawing"). Pure: no database.

The bank here is the real `backend/data/interest_test.json`, keyed by question
number, so the tests exercise the same area spread the app uses.
"""

import json
import random
from collections import Counter
from pathlib import Path

from app.services.question_sets import MAX_PER_AREA, MIN_PER_AREA, SET_SIZE, draw_set, is_balanced

DATA = json.loads((Path(__file__).resolve().parents[1] / "data" / "interest_test.json").read_text(encoding="utf-8"))
BANK = {q["n"]: {area for _, area in q["options"]} for q in DATA["questions"]}


def _area_counts(ids):
    return Counter(area for q in ids for area in BANK[q])


def test_set_has_40_different_questions_and_is_balanced_across_500_draws():
    rng = random.Random(2026)
    for _ in range(500):
        chosen = draw_set(BANK, [], rng)
        assert len(chosen) == SET_SIZE
        assert len(set(chosen)) == SET_SIZE
        counts = _area_counts(chosen)
        assert set(counts) == set(DATA["areas"])
        assert all(MIN_PER_AREA <= c <= MAX_PER_AREA for c in counts.values()), counts


def test_new_sets_avoid_every_seen_question_while_40_unseen_remain():
    # 300 questions / 40 per set: sets 1-7 can all be fully fresh (280 questions).
    rng = random.Random(7)
    past: list[list[int]] = []
    for _ in range(7):
        chosen = draw_set(BANK, past, rng)
        seen = {q for s in past for q in s}
        assert not seen & set(chosen)
        assert is_balanced(chosen, BANK), _area_counts(chosen)
        past.append(chosen)


def test_when_fewer_than_40_unseen_remain_all_are_used_and_none_from_the_last_set():
    rng = random.Random(11)
    past: list[list[int]] = []
    for _ in range(7):
        past.append(draw_set(BANK, past, rng))
    unseen = set(BANK) - {q for s in past for q in s}
    assert len(unseen) == 20

    eighth = draw_set(BANK, past, rng)
    assert len(set(eighth)) == SET_SIZE
    assert unseen <= set(eighth)
    assert not set(past[-1]) & set(eighth)


def test_same_seed_gives_the_same_set():
    assert draw_set(BANK, [], random.Random(42)) == draw_set(BANK, [], random.Random(42))


def test_impossible_balance_still_returns_a_full_set():
    # 50 hand-made questions that all offer the same 4 areas: no set of 40 can
    # keep those areas at 20 or fewer, or give the other 5 areas any share.
    lopsided = {n: {"ST", "BM", "LG", "HS"} for n in range(1, 51)}
    lopsided[51] = {"AD", "EH", "HT", "AE"}
    chosen = draw_set(lopsided, [], random.Random(1))
    assert len(set(chosen)) == SET_SIZE
    assert not is_balanced(chosen, lopsided)
