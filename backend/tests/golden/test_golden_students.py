"""Golden-student tests for `GET /me/analysis` (Phase 5 stage 3; PRD T1, T2).

Six hand-derived sample students, registered and driven through the real API
(`PUT /me/results`, `PUT /me/interest-answers`, `GET /me/analysis`) against
the real, migrated test database (see `tests/conftest.py`) -- no mocking of
`scoring.py` / `eligibility.py` / `analysis.py`. Input data lives in
`tests/golden/students.json`; expected chart output lives in
`tests/golden/expected/<name>.json`. Every expected number in the `expected/`
files was independently re-derived from the same grades/picks using the
formulas documented in each file's `_derivation` field -- see those files
for two arithmetic corrections found in the original hand-derived draft
(Amir/Mei Ling's LANGUAGES+HUMANITIES subject-group scores, and Rahman's
HUMANITIES subject-group score / Education & Humanities excel score).

A separate section (bottom of this file) spot-checks 3 real UPU programs'
eligibility verdicts by calling `evaluate_eligibility` directly with grades
+ rules loaded from the live `GET /programs/{code}` endpoint, rather than
relying on Best Fit's top-3-by-name truncation to surface them.
"""

import json
import uuid
from pathlib import Path

from sqlalchemy import select

from app.models.interest_test import InterestQuestion, InterestTestSet, InterestTestSetQuestion
from app.services.analysis import BUMIPUTERA_RACES
from app.services.eligibility import evaluate_eligibility, find_matching
from app.services.explanations import explain_program

FIXED_SET_SIZE = 40
GOLDEN_DIR = Path(__file__).parent
STUDENTS = json.loads((GOLDEN_DIR / "students.json").read_text(encoding="utf-8"))["students"]
STUDENTS_BY_NAME = {s["name"]: s for s in STUDENTS}


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _register_and_login(client, make_register_payload, student: dict):
    payload = make_register_payload(
        is_citizen=student["is_citizen"],
        race=student["race"],
        spm_year=student["spm_year"],
    )
    register_response = client.post("/auth/register", json=payload)
    assert register_response.status_code == 201, register_response.text
    login_response = client.post("/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert login_response.status_code == 200, login_response.text
    return login_response.json()["access_token"], uuid.UUID(register_response.json()["id"])


def _give_fixed_set(db_session, user_id: uuid.UUID) -> None:
    """Phase 9 (rotation plan Step 9.2 task 8): give the student a fixed set --
    bank questions 1-40, in order -- instead of a random draw, so the expected
    numbers never depend on randomness. In that set, Healthcare & Social
    Services and Media & Communications are offered by 17 questions each, and
    every other area by 18."""
    question_ids = dict(
        db_session.execute(
            select(InterestQuestion.n, InterestQuestion.id).where(InterestQuestion.n.between(1, FIXED_SET_SIZE))
        ).all()
    )
    test_set = InterestTestSet(user_id=user_id)
    db_session.add(test_set)
    db_session.flush()
    for n in range(1, FIXED_SET_SIZE + 1):
        db_session.add(InterestTestSetQuestion(set_id=test_set.id, position=n, question_id=question_ids[n]))
    db_session.flush()


def _resolve_interest_picks(client, token: str, picks: list[dict]) -> list[dict]:
    """Turn `[{"question_text": ..., "option_text": ...}, ...]` into
    `[{"question_id": ..., "option_id": ...}, ...]` by matching the exact
    `text` fields of the student's current set from `GET /me/interest-test`.
    """
    questions = client.get("/me/interest-test", headers=_auth(token)).json()["questions"]
    by_text = {q["text"]: q for q in questions}
    resolved = []
    for pick in picks:
        question = by_text[pick["question_text"]]
        option = next(opt for opt in question["options"] if opt["text"] == pick["option_text"])
        resolved.append({"question_id": question["id"], "option_id": option["id"]})
    return resolved


def _run_student(client, make_register_payload, db_session, student: dict) -> dict:
    """Register, PUT results, optionally PUT interest answers, and return
    the `GET /me/analysis` body for one golden student.
    """
    token, user_id = _register_and_login(client, make_register_payload, student)

    put_results_resp = client.put("/me/results", json=student["results"], headers=_auth(token))
    assert put_results_resp.status_code == 200, put_results_resp.text

    if student["call_interest_answers"]:
        _give_fixed_set(db_session, user_id)
        resolved = _resolve_interest_picks(client, token, student["interest_picks"])
        put_answers_resp = client.put("/me/interest-answers", json=resolved, headers=_auth(token))
        assert put_answers_resp.status_code == 200, put_answers_resp.text

    analysis_resp = client.get("/me/analysis", headers=_auth(token))
    assert analysis_resp.status_code == 200, analysis_resp.text
    return analysis_resp.json()


def _group_score(body: dict, group_code: str) -> float:
    return next(g["score"] for g in body["subject_groups"] if g["group"] == group_code)


def _group_present(body: dict, group_code: str) -> bool:
    return any(g["group"] == group_code for g in body["subject_groups"])


def _area_score(body: dict, area_name: str) -> float:
    return next(a["score"] for a in body["interest_areas"] if a["area"] == area_name)


def _assert_matches_expected(body: dict, expected: dict) -> None:
    # --- subject_groups: name-keyed lookups, plus explicit absence checks ---
    for group_code, score in expected["subject_groups"].items():
        assert _group_score(body, group_code) == score, group_code
    for absent_group in expected.get("subject_groups_absent", []):
        assert not _group_present(body, absent_group), absent_group
    assert len(body["subject_groups"]) == len(expected["subject_groups"])

    # --- interest_areas: name-keyed lookups, all 9 always present ---
    assert len(body["interest_areas"]) == 9
    for area_name, score in expected["interest_areas"].items():
        assert _area_score(body, area_name) == score, area_name

    # --- likely_to_excel / likely_to_love / sweet_spots: exact ordered lists ---
    assert [[e["area"], e["score"]] for e in body["likely_to_excel"]] == expected["likely_to_excel"]
    assert [[e["area"], e["score"]] for e in body["likely_to_love"]] == expected["likely_to_love"]
    for absent_area in expected.get("likely_to_excel_absent", []):
        assert absent_area not in [e["area"] for e in body["likely_to_excel"]], absent_area
    assert body["sweet_spots"] == expected["sweet_spots"]

    assert body["category"] == expected["category"]
    assert body["interest_test_complete"] == expected["interest_test_complete"]


def _load_expected(name: str) -> dict:
    return json.loads((GOLDEN_DIR / "expected" / f"{name}.json").read_text(encoding="utf-8"))


# --- Amir: Melayu, citizen, spm_year 2025 (category A) ------------------------


def test_amir(client, make_register_payload, db_session):
    student = STUDENTS_BY_NAME["amir"]
    expected = _load_expected("amir")

    body = _run_student(client, make_register_payload, db_session, student)
    _assert_matches_expected(body, expected)

    best_fit_areas = {area["area"] for area in body["best_fit"]}
    assert best_fit_areas == set(expected["best_fit_areas"])


# --- Mei Ling: identical results/answers to Amir, only race differs -----------


def test_mei_ling_matches_amir_because_race_never_affects_scoring(client, make_register_payload, db_session):
    amir_body = _run_student(client, make_register_payload, db_session, STUDENTS_BY_NAME["amir"])
    mei_ling_body = _run_student(client, make_register_payload, db_session, STUDENTS_BY_NAME["mei_ling"])
    expected = _load_expected("mei_ling")

    _assert_matches_expected(mei_ling_body, expected)

    # Direct equality against Amir's own (freshly computed, same run) body --
    # race must never affect the pure scoring/chart functions.
    for field in ("subject_groups", "interest_areas", "likely_to_excel", "likely_to_love", "sweet_spots", "category"):
        assert mei_ling_body[field] == amir_body[field], field


# --- Priya: India, citizen, spm_year 2020 (category B) ------------------------


def test_priya(client, make_register_payload, db_session):
    body = _run_student(client, make_register_payload, db_session, STUDENTS_BY_NAME["priya"])
    _assert_matches_expected(body, _load_expected("priya"))


# --- Rahman: Anak Negeri Sabah, citizen, spm_year 2025 (category A), no interest test ---


def test_rahman(client, make_register_payload, db_session):
    body = _run_student(client, make_register_payload, db_session, STUDENTS_BY_NAME["rahman"])
    _assert_matches_expected(body, _load_expected("rahman"))


# --- Aisyah: Melayu, citizen, spm_year 2025 (category A), no science subjects ---


def test_aisyah(client, make_register_payload, db_session):
    body = _run_student(client, make_register_payload, db_session, STUDENTS_BY_NAME["aisyah"])
    _assert_matches_expected(body, _load_expected("aisyah"))


# --- Daniel: non-citizen, spm_year 2025 (category A), good grades -------------


def test_daniel(client, make_register_payload, db_session):
    body = _run_student(client, make_register_payload, db_session, STUDENTS_BY_NAME["daniel"])
    expected = _load_expected("daniel")
    _assert_matches_expected(body, expected)

    assert expected["best_fit_all_programs_empty"] is True
    assert body["best_fit"] != []
    for area in body["best_fit"]:
        assert area["programs"] == []


# --- Eligibility spot-checks: evaluate_eligibility called directly ------------
#
# These do not rely on Best Fit's top-3-by-name truncation to surface a
# program -- a program can be genuinely Eligible for a student yet not make
# an area's top-3-by-name cut if other eligible programs sort earlier
# alphabetically. Instead: fetch the program's `requirements` /
# `general_requirements` via `GET /programs/{code}`, pick the category-A row,
# and call `evaluate_eligibility` directly.


# --- "Why this diploma?" (result explanations PRD; plan Step 10.1 task 7) ------
#
# Expected lines are worked out by hand from each program's real category-A
# rules (via `GET /programs/{code}`) and the student's grades, using the plan's
# fixed order: named-subject rules first, "N more subjects" rules last, and
# candidates best grade first, then subject code.

AMIR_SCIENCE_TECH_AREA_LINES = [
    # Excel: mean(Mathematics 100, Sciences mean(FZ 100, KM 88.9, BL 88.9) = 92.6,
    # Technical & ICT 100) = 97.5. Love: 9 picks / 18 offered in the fixed set = 50.
    "Science & Technology is #1 in what you're likely to excel in, at 97.5%, "
    "from your Mathematics (100%), Sciences (92.6%) and Technical & ICT (100%) grades.",
    "Science & Technology is #1 in what you're likely to love, at 50%: "
    "you picked a Science & Technology answer in 9 of the 18 questions that offered one.",
    "That makes it a Sweet spot: it's in your top 3 for both what you're likely to excel in "
    "and what you're likely to love.",
]


def _subject_names(client) -> dict[str, str]:
    return {s["code"]: s["name_ms"] for s in client.get("/subjects").json()}


def _explain_real_program(client, code: str, grades: dict[str, str], **context) -> dict:
    program = client.get(f"/programs/{code}").json()
    general_rules, program_rules = _category_a_rules(program)
    return explain_program(
        program={"nec_code": program["nec_code"], "nec_name": program["nec_name"], **context.pop("verdict")},
        area=context.pop("area"),
        grades=grades,
        subject_names=_subject_names(client),
        matching=find_matching(general_rules, program_rules, grades),
        bumiputera_only=bool(general_rules.get("bumiputera_only") or program_rules.get("bumiputera_only")),
        **context,
    )


def test_why_amir_ue4481001_lists_every_rule_with_the_grade_that_meets_it(client):
    why = _explain_real_program(
        client,
        "UE4481001",
        _grades_of("amir"),
        verdict={"verdict": "Eligible", "reasons": []},
        area="Science & Technology",
        excel=None,
        love=None,
        position=1,
        total=1,
    )
    # Named rules: BM, SJ, BI, MT, then "1 of 15 listed" -> best of MTT/FZ/KM/BL/SK
    # = A+ FZ, MTT, SK -> FZ by code. General "2 more" from MTT A+, SK A+, BL A,
    # KM A, EK C -> MTT, SK. Diploma "2 more" from BL A, KM A, EK C -> BL, KM.
    assert why["rules"] == [
        {
            "title": "General UPU rules (syarat am)",
            "lines": [
                "Bahasa Melayu: needs C, you have A+",
                "Sejarah: needs E, you have A",
                "2 more subjects at C or better: Matematik Tambahan (A+), Sains Komputer (A+)",
            ],
        },
        {
            "title": "This diploma's rules (syarat khas)",
            "lines": [
                "Bahasa Inggeris: needs C, you have A",
                "Matematik: needs C, you have A+",
                "At least C in 1 of 15 listed subjects: Fizik (A+)",
                "2 more subjects at C or better: Biologi (A), Kimia (A)",
                "Only open to Bumiputera students, and you qualify.",
            ],
        },
    ]
    assert why["match"][0] == "This is a computing diploma: its field of study, Sains Komputer (code 0613), is part of Science & Technology."
    assert why["still_needed"] == ["Nothing else needed. No interview or test."]


def test_why_rahman_ue4213001_is_conditional_with_no_extra_rules(client):
    why = _explain_real_program(
        client,
        "UE4213001",
        _grades_of("rahman"),
        verdict={"verdict": "Conditional", "reasons": ["Requires interview/test"]},
        area="Arts & Design",
        excel=None,
        love=None,
        position=1,
        total=1,
    )
    # "2 more" from BI C, GG C, EK C (all C) -> code order BI, EK.
    assert why["rules"] == [
        {
            "title": "General UPU rules (syarat am)",
            "lines": [
                "Bahasa Melayu: needs C, you have C",
                "Sejarah: needs E, you have D",
                "2 more subjects at C or better: Bahasa Inggeris (C), Ekonomi (C)",
            ],
        },
        {"title": "This diploma's rules (syarat khas)", "lines": ["No extra subject rules beyond the general ones."]},
    ]
    assert why["still_needed"] == ["You'll need to pass an interview or test."]


def test_why_is_on_every_best_fit_diploma_and_matches_amirs_scores(client, make_register_payload, db_session):
    body = _run_student(client, make_register_payload, db_session, STUDENTS_BY_NAME["amir"])
    assert body["best_fit"], "Amir should have Best Fit areas"

    science_tech = next(area for area in body["best_fit"] if area["area"] == "Science & Technology")
    assert science_tech["programs"], "Amir should have Science & Technology diplomas"
    for area in body["best_fit"]:
        for position, program in enumerate(area["programs"], start=1):
            why = program["why"]
            assert why["match"][0].endswith(f"is part of {area['area']}.")
            assert [section["title"] for section in why["rules"]] == [
                "General UPU rules (syarat am)",
                "This diploma's rules (syarat khas)",
            ]
            assert all(section["lines"] for section in why["rules"])
            assert why["still_needed"]
            assert why["position"].startswith(f"{position} of ")
            assert why["position"].split(" of ")[1].split(" ")[0].isdigit()
            total = int(why["position"].split(" of ")[1].split(" ")[0])
            assert total >= len(area["programs"])
            if program["verdict"] == "Eligible":
                assert why["still_needed"] == ["Nothing else needed. No interview or test."]
    for program in science_tech["programs"]:
        assert program["why"]["match"][1:] == AMIR_SCIENCE_TECH_AREA_LINES


def test_why_never_shows_race_or_interest_test_wording(client, make_register_payload, db_session):
    body = _run_student(client, make_register_payload, db_session, STUDENTS_BY_NAME["mei_ling"])
    whys = json.dumps([p["why"] for area in body["best_fit"] for p in area["programs"]], ensure_ascii=False)
    assert whys != "[]"
    assert "Cina" not in whys
    assert "—" not in whys and "–" not in whys
    # No interest test question, and no answer long enough to be recognisable
    # (very short answers like "Law" could match an area name by chance).
    bank = json.loads((GOLDEN_DIR.parents[1] / "data" / "interest_test.json").read_text(encoding="utf-8"))
    for question in bank["questions"]:
        assert question["text"] not in whys
        for option_text, _ in question["options"]:
            if len(option_text) > 20:
                assert option_text not in whys


def _category_a_rules(program: dict) -> tuple[dict, dict]:
    general_rules = next(r["rules"] for r in program["general_requirements"] if r["category"] == "A")
    program_rules = next(r["rules"] for r in program["requirements"] if r["category"] == "A")
    return general_rules, program_rules


def _grades_of(name: str) -> dict[str, str]:
    return {row["subject_code"]: row["grade"] for row in STUDENTS_BY_NAME[name]["results"]}


def test_eligibility_spot_checks(client):
    amir_grades = _grades_of("amir")
    mei_ling_grades = _grades_of("mei_ling")
    rahman_grades = _grades_of("rahman")

    # --- 1. UE4481001: bumiputera_only=true, category A syarat khas needs
    # BI>=C, MT>=C, one_of(...)>=C count 1, plus 2 uncounted@C, and the
    # general syarat am's own BM>=C / SJ>=E / 2 uncounted@C. ---------------
    ue4481001 = client.get("/programs/UE4481001").json()
    general_rules, program_rules = _category_a_rules(ue4481001)
    assert program_rules["bumiputera_only"] is True

    amir_verdict = evaluate_eligibility(
        amir_grades, general_rules, program_rules, is_citizen=True, is_bumiputera="Melayu" in BUMIPUTERA_RACES
    )
    assert amir_verdict == {"verdict": "Eligible", "reasons": []}

    mei_ling_verdict = evaluate_eligibility(
        mei_ling_grades, general_rules, program_rules, is_citizen=True, is_bumiputera="Cina" in BUMIPUTERA_RACES
    )
    assert mei_ling_verdict == {
        "verdict": "Not Eligible",
        "reasons": ["This program is limited to Bumiputera students"],
    }

    # --- 2. UA4481001 (non-UiTM, non-Bumiputera-only equivalent): Mei Ling
    # is Eligible here even though she's Not Eligible for UE4481001. -------
    ua4481001 = client.get("/programs/UA4481001").json()
    general_rules_2, program_rules_2 = _category_a_rules(ua4481001)

    mei_ling_verdict_2 = evaluate_eligibility(
        mei_ling_grades, general_rules_2, program_rules_2, is_citizen=True, is_bumiputera="Cina" in BUMIPUTERA_RACES
    )
    assert mei_ling_verdict_2 == {"verdict": "Eligible", "reasons": []}

    # --- 3. UE4213001 (UiTM, no syarat khas grade requirements, interview
    # required): Rahman is Conditional (grade tree passes via the general
    # syarat am alone; interview: true forces Conditional). ----------------
    ue4213001 = client.get("/programs/UE4213001").json()
    general_rules_3, program_rules_3 = _category_a_rules(ue4213001)

    rahman_verdict = evaluate_eligibility(
        rahman_grades,
        general_rules_3,
        program_rules_3,
        is_citizen=True,
        is_bumiputera="Anak Negeri Sabah" in BUMIPUTERA_RACES,
    )
    assert rahman_verdict == {"verdict": "Conditional", "reasons": ["Requires interview/test"]}
