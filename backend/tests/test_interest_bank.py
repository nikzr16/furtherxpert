"""Data checks on the question bank `backend/data/interest_test.json`
(rotation PRD criteria 1, 2, 11; rotation plan Step 9.1 task 5). No database.
"""

import json
from collections import Counter
from pathlib import Path

DATA = json.loads((Path(__file__).resolve().parents[1] / "data" / "interest_test.json").read_text(encoding="utf-8"))
QUESTIONS = DATA["questions"]


def test_bank_has_300_questions_numbered_1_to_300():
    assert [q["n"] for q in QUESTIONS] == list(range(1, 301))


def test_every_question_has_4_answers_in_4_different_known_areas():
    for q in QUESTIONS:
        areas = [area for _, area in q["options"]]
        assert len(areas) == 4, q["n"]
        assert len(set(areas)) == 4, q["n"]
        assert set(areas) <= set(DATA["areas"]), q["n"]
        assert all(text.strip() for text, _ in q["options"]), q["n"]
    # "None of the above" is added to every question by the migrations.
    assert DATA["none_option"] == "None of the above"


def test_no_duplicate_question_or_answer_text():
    question_texts = Counter(q["text"].strip().lower() for q in QUESTIONS)
    assert [t for t, c in question_texts.items() if c > 1] == []
    answer_texts = Counter(text.strip().lower() for q in QUESTIONS for text, _ in q["options"])
    assert [t for t, c in answer_texts.items() if c > 1] == []


def test_every_area_is_tagged_133_or_134_times():
    counts = Counter(area for q in QUESTIONS for _, area in q["options"])
    assert set(counts) == set(DATA["areas"])
    # 300 questions x 4 answers = 1,200 tags; 1,200 / 9 areas = 133.3.
    assert sorted(counts.values()) == [133] * 6 + [134] * 3


def test_bank_records_who_drafted_and_reviewed_the_new_questions():
    bank = DATA["bank"]
    assert "product owner" in bank["questions_1_20"]
    assert bank["questions_21_300_drafted_by"]
    assert "did not review these questions one by one" in bank["questions_21_300_reviewed_by"]
