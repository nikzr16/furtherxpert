"""API tests for `GET /me/analysis` (PRD T1, T2, T5, T6; plan Phase 5 stage 2).

Runs against the real, separate test database (see `tests/conftest.py`),
already migrated with reference data (subjects, UPU snapshot, interest test)
before any test runs. Real subject codes / real seeded data are looked up
through the DB session or the public reference endpoints rather than
hardcoding assumptions about what exists, except for `BM`/`SJ`/`MT`/`PSV`
which are already relied on by `tests/test_student_input.py` and are
guaranteed present (BM/SJ are required by every `PUT /me/results` call).
"""

from sqlalchemy import select

from app.models.interest_test import InterestOption
from app.models.session import Session as UpuSession


def _register_and_login(client, make_register_payload, **overrides):
    payload = make_register_payload(**overrides)
    register_response = client.post("/auth/register", json=payload)
    assert register_response.status_code == 201
    login_response = client.post("/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return payload, token, register_response.json()["id"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _put_results(client, token, items):
    resp = client.put("/me/results", json=items, headers=_auth(token))
    assert resp.status_code == 200
    return resp.json()


def _first_two_questions(client) -> list[dict]:
    questions = client.get("/interest-test").json()
    return questions[:2]


def _non_none_option(question: dict) -> dict:
    return next(opt for opt in question["options"] if opt["text"] != "None of the above")


def _none_option(question: dict) -> dict:
    return next(opt for opt in question["options"] if opt["text"] == "None of the above")


def _area_name_for_option(db_session, option_id: int) -> str:
    from app.models.interest_area import InterestArea

    option = db_session.get(InterestOption, option_id)
    area = db_session.get(InterestArea, option.area_id)
    return area.name


# --- Structural shape, no saved data -----------------------------------------


def test_analysis_empty_state_returns_200_with_both_chart_sections(client, make_register_payload):
    _, token, _ = _register_and_login(client, make_register_payload)

    resp = client.get("/me/analysis", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()

    assert set(body.keys()) == {
        "subject_groups",
        "interest_areas",
        "likely_to_excel",
        "likely_to_love",
        "sweet_spots",
        "best_fit",
        "category",
        "computed_at",
    }
    # Chart 2 (interest areas) is never omitted -- all 9 seeded areas appear
    # even with zero picks (PRD T1, skill S2).
    assert len(body["interest_areas"]) == 9
    assert all(entry["score"] == 0.0 for entry in body["interest_areas"])
    # Chart 1 (subject groups) is omitted entirely when no results are saved
    # (PRD T1: "A group with no subjects taken is hidden").
    assert body["subject_groups"] == []
    assert body["category"] in ("A", "B")


# --- Cross-user isolation -----------------------------------------------------


def test_cross_user_isolation(client, make_register_payload):
    _, token_a, _ = _register_and_login(client, make_register_payload)
    _, token_b, _ = _register_and_login(client, make_register_payload)

    _put_results(client, token_a, [{"subject_code": "BM", "grade": "A+"}, {"subject_code": "SJ", "grade": "E"}])
    _put_results(client, token_b, [{"subject_code": "BM", "grade": "D"}, {"subject_code": "SJ", "grade": "E"}])

    body_a = client.get("/me/analysis", headers=_auth(token_a)).json()
    body_b = client.get("/me/analysis", headers=_auth(token_b)).json()

    languages_a = next(g["score"] for g in body_a["subject_groups"] if g["group"] == "LANGUAGES")
    languages_b = next(g["score"] for g in body_b["subject_groups"] if g["group"] == "LANGUAGES")
    assert languages_a != languages_b
    # A's response never leaks B's (different) score, and vice versa.
    assert body_a["subject_groups"] != body_b["subject_groups"]


# --- Cache invalidation on results change -------------------------------------


def test_cache_invalidation_on_results_change(client, make_register_payload):
    _, token, _ = _register_and_login(client, make_register_payload)
    _put_results(client, token, [{"subject_code": "BM", "grade": "D"}, {"subject_code": "SJ", "grade": "E"}])

    first = client.get("/me/analysis", headers=_auth(token)).json()
    first_languages = next(g["score"] for g in first["subject_groups"] if g["group"] == "LANGUAGES")

    # A second GET without any save in between must be served from cache
    # (same computed_at) -- proves the cache is actually being used.
    again = client.get("/me/analysis", headers=_auth(token)).json()
    assert again["computed_at"] == first["computed_at"]

    # Changing BM's grade (a subject the student already has) must
    # invalidate the cache so the next read recomputes, not serve stale data.
    _put_results(client, token, [{"subject_code": "BM", "grade": "A+"}, {"subject_code": "SJ", "grade": "E"}])
    second = client.get("/me/analysis", headers=_auth(token)).json()
    second_languages = next(g["score"] for g in second["subject_groups"] if g["group"] == "LANGUAGES")

    assert second_languages != first_languages
    assert second["computed_at"] != first["computed_at"]


# --- Cache invalidation on answers change -------------------------------------


def test_cache_invalidation_on_answers_change(client, make_register_payload, db_session):
    _, token, _ = _register_and_login(client, make_register_payload)
    q1, _q2 = _first_two_questions(client)
    tagged_option = _non_none_option(q1)
    area_name = _area_name_for_option(db_session, tagged_option["id"])

    put_resp = client.put(
        "/me/interest-answers",
        json=[{"question_id": q1["id"], "option_id": tagged_option["id"]}],
        headers=_auth(token),
    )
    assert put_resp.status_code == 200

    first = client.get("/me/analysis", headers=_auth(token)).json()
    first_score = next(a["score"] for a in first["interest_areas"] if a["area"] == area_name)
    assert first_score > 0.0

    # A second GET without any save in between must be served from cache.
    again = client.get("/me/analysis", headers=_auth(token)).json()
    assert again["computed_at"] == first["computed_at"]

    # Retake: switch q1's answer to "None of the above" -- the tagged
    # area's pick count (and therefore score) must drop, and the cache must
    # have been invalidated so this is visible immediately.
    none_option = _none_option(q1)
    retake_resp = client.put(
        "/me/interest-answers",
        json=[{"question_id": q1["id"], "option_id": none_option["id"]}],
        headers=_auth(token),
    )
    assert retake_resp.status_code == 200

    second = client.get("/me/analysis", headers=_auth(token)).json()
    second_score = next(a["score"] for a in second["interest_areas"] if a["area"] == area_name)

    assert second_score < first_score
    assert second["computed_at"] != first["computed_at"]


# --- Likely to love excludes 0-score areas (decision 0007) --------------------


def test_love_list_holds_one_item_when_only_one_area_has_a_nonzero_score(client, make_register_payload, db_session):
    _, token, _ = _register_and_login(client, make_register_payload)
    q1, _q2 = _first_two_questions(client)
    tagged_option = _non_none_option(q1)
    area_name = _area_name_for_option(db_session, tagged_option["id"])

    put_resp = client.put(
        "/me/interest-answers",
        json=[{"question_id": q1["id"], "option_id": tagged_option["id"]}],
        headers=_auth(token),
    )
    assert put_resp.status_code == 200

    body = client.get("/me/analysis", headers=_auth(token)).json()

    # Only one area has any picks at all (every other area's own Chart 2
    # score is still 0.0), so the love top-3 list holds exactly that one
    # area -- it is never padded to 3 with 0-score filler.
    assert len(body["likely_to_love"]) == 1
    assert body["likely_to_love"][0]["area"] == area_name
    assert body["likely_to_love"][0]["score"] > 0.0


def test_love_list_is_empty_when_interest_test_never_taken_but_excel_and_charts_unaffected(
    client, make_register_payload
):
    _, token, _ = _register_and_login(client, make_register_payload)
    _put_results(
        client,
        token,
        [
            {"subject_code": "BM", "grade": "A+"},
            {"subject_code": "SJ", "grade": "A+"},
            {"subject_code": "MT", "grade": "A+"},
            {"subject_code": "PSV", "grade": "A+"},
        ],
    )

    body = client.get("/me/analysis", headers=_auth(token)).json()

    # No interest-test answers were ever saved -- every one of the 9 areas
    # stays at 0.0 (Chart 2 is never omitted), so the love top-3 is empty.
    assert len(body["interest_areas"]) == 9
    assert all(entry["score"] == 0.0 for entry in body["interest_areas"])
    assert body["likely_to_love"] == []

    # "Likely to excel" and the charts are unaffected by the love-list rule
    # change -- they're still computed normally from the saved grades.
    assert body["subject_groups"] != []
    assert body["likely_to_excel"] != []


# --- Non-citizen: Best Fit programs are always empty, charts still shown -----


def test_non_citizen_best_fit_has_no_programs_but_charts_still_shown(client, make_register_payload):
    _, token, _ = _register_and_login(client, make_register_payload, is_citizen=False)

    _put_results(
        client,
        token,
        [
            {"subject_code": "BM", "grade": "A+"},
            {"subject_code": "SJ", "grade": "A+"},
            {"subject_code": "MT", "grade": "A+"},
            {"subject_code": "PSV", "grade": "A+"},
        ],
    )

    body = client.get("/me/analysis", headers=_auth(token)).json()

    # Charts are still fully computed for a non-citizen (PRD T2: "The charts
    # are still shown").
    assert body["subject_groups"] != []
    assert len(body["interest_areas"]) == 9
    assert body["likely_to_excel"] != []
    # This test never saves interest-test answers, so every interest score
    # is 0.0 and likely_to_love is correctly empty under decision 0007's
    # 0-score exclusion -- it is likely_to_excel (grade-based, unaffected by
    # that rule) that proves the charts are still fully computed here.
    assert body["likely_to_love"] == []

    # But a non-citizen can never be Eligible/Conditional for any program
    # (PRD T2 hard stop), so Best Fit's program lists must all be empty --
    # never full of "Not Eligible" entries (PRD T1: "only Eligible or
    # Conditional ones ... never Not Eligible").
    assert body["best_fit"] != []
    for area in body["best_fit"]:
        assert area["programs"] == []


# --- Category A vs B (PRD T2) --------------------------------------------------


def test_category_a_vs_b(client, make_register_payload, db_session):
    session = db_session.execute(select(UpuSession).order_by(UpuSession.created_at.desc()).limit(1)).scalar_one()
    latest_spm_year = session.latest_spm_year

    _, token_a, _ = _register_and_login(client, make_register_payload, spm_year=latest_spm_year)
    _, token_b, _ = _register_and_login(client, make_register_payload, spm_year=latest_spm_year - 3)

    body_a = client.get("/me/analysis", headers=_auth(token_a)).json()
    body_b = client.get("/me/analysis", headers=_auth(token_b)).json()

    assert body_a["category"] == "A"
    assert body_b["category"] == "B"


# --- Auth is required ----------------------------------------------------------


def test_analysis_requires_auth(client):
    resp = client.get("/me/analysis")
    assert resp.status_code in (401, 403)


def test_analysis_rejects_garbage_token(client):
    resp = client.get("/me/analysis", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401
