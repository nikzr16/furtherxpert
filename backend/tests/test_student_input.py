"""API tests for student input (PRD T1, T2, T6; plan Phase 4 Check):
`GET/PUT /me/results`, `GET/PUT /me/interest-answers`.

Runs against the real, separate test database (see `tests/conftest.py`),
already migrated with the reference-data (subjects) and the seeded interest
test (Phase 4 data migration) before any test runs.
"""

from sqlalchemy import select

from app.models.interest_test import InterestAnswer
from app.models.spm_result import SPMResult


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


# --- GET/PUT /me/results ---------------------------------------------------


def test_put_results_rejects_bad_grades(client, make_register_payload):
    _, token, _ = _register_and_login(client, make_register_payload)

    for bad_grade in ("B-", "C-", "F"):
        resp = client.put(
            "/me/results",
            json=[
                {"subject_code": "BM", "grade": bad_grade},
                {"subject_code": "SJ", "grade": "E"},
            ],
            headers=_auth(token),
        )
        assert resp.status_code == 422, bad_grade


def test_put_results_rejects_unknown_subject(client, make_register_payload):
    _, token, _ = _register_and_login(client, make_register_payload)

    resp = client.put(
        "/me/results",
        json=[
            {"subject_code": "BM", "grade": "C"},
            {"subject_code": "SJ", "grade": "E"},
            {"subject_code": "NOT-A-REAL-SUBJECT", "grade": "A"},
        ],
        headers=_auth(token),
    )
    assert resp.status_code == 400
    assert "NOT-A-REAL-SUBJECT" in resp.json()["detail"]


def test_put_results_requires_bm_and_sejarah(client, make_register_payload):
    _, token, _ = _register_and_login(client, make_register_payload)

    resp = client.put(
        "/me/results",
        json=[{"subject_code": "MT", "grade": "A"}],
        headers=_auth(token),
    )
    assert resp.status_code == 400
    detail = resp.json()["detail"]
    assert "BM" in detail
    assert "SJ" in detail


def test_put_results_rejects_duplicate_subject_in_payload(client, make_register_payload):
    _, token, _ = _register_and_login(client, make_register_payload)

    resp = client.put(
        "/me/results",
        json=[
            {"subject_code": "BM", "grade": "C"},
            {"subject_code": "BM", "grade": "B"},
            {"subject_code": "SJ", "grade": "E"},
        ],
        headers=_auth(token),
    )
    assert resp.status_code == 400


def test_put_results_upserts_without_dropping_omitted_subjects(client, make_register_payload):
    _, token, _ = _register_and_login(client, make_register_payload)

    first = client.put(
        "/me/results",
        json=[
            {"subject_code": "BM", "grade": "C"},
            {"subject_code": "SJ", "grade": "E"},
            {"subject_code": "MT", "grade": "B"},
        ],
        headers=_auth(token),
    )
    assert first.status_code == 200
    first_grades = {r["subject_code"]: r["grade"] for r in first.json()}
    assert first_grades == {"BM": "C", "SJ": "E", "MT": "B"}

    # Re-save with just BM's grade changed; MT (omitted this time) must
    # still be there afterwards -- PUT /me/results upserts, it doesn't
    # delete a subject the payload happens to omit (PRD T6).
    second = client.put(
        "/me/results",
        json=[
            {"subject_code": "BM", "grade": "A"},
            {"subject_code": "SJ", "grade": "E"},
        ],
        headers=_auth(token),
    )
    assert second.status_code == 200

    get_resp = client.get("/me/results", headers=_auth(token))
    assert get_resp.status_code == 200
    grades = {r["subject_code"]: r["grade"] for r in get_resp.json()}
    assert grades == {"BM": "A", "SJ": "E", "MT": "B"}


def test_results_are_scoped_to_the_caller(client, make_register_payload):
    _, token_a, _ = _register_and_login(client, make_register_payload)
    _, token_b, _ = _register_and_login(client, make_register_payload)

    put_a = client.put(
        "/me/results",
        json=[{"subject_code": "BM", "grade": "A"}, {"subject_code": "SJ", "grade": "E"}],
        headers=_auth(token_a),
    )
    assert put_a.status_code == 200

    # B never saved any results -- B's own GET must be empty, never A's rows.
    get_b = client.get("/me/results", headers=_auth(token_b))
    assert get_b.status_code == 200
    assert get_b.json() == []


def test_results_require_auth(client):
    resp = client.get("/me/results")
    assert resp.status_code in (401, 403)
    resp = client.put("/me/results", json=[])
    assert resp.status_code in (401, 403)


# --- PUT /me/interest-answers ------------------------------------------------
# (The question set itself is covered in tests/test_interest_sets.py.)


def _set_questions(client, token) -> list[dict]:
    return client.get("/me/interest-test", headers=_auth(token)).json()["questions"]


def _first_two_questions_with_options(client, token) -> list[dict]:
    return _set_questions(client, token)[:2]


def test_put_interest_answers_happy_path_and_partial_saves_merge(client, make_register_payload, db_session):
    """A partial `PUT` is a merge/upsert (decision 0008), not a full
    replace: a later save that omits a question must not delete that
    question's previously-saved answer, and re-sending a question must
    update it in place."""
    _, token, user_id = _register_and_login(client, make_register_payload)
    q1, q2 = _first_two_questions_with_options(client, token)

    first_payload = [
        {"question_id": q1["id"], "option_id": q1["options"][0]["id"]},
        {"question_id": q2["id"], "option_id": q2["options"][1]["id"]},
    ]
    first_resp = client.put("/me/interest-answers", json=first_payload, headers=_auth(token))
    assert first_resp.status_code == 200
    assert {(a["question_id"], a["option_id"]) for a in first_resp.json()} == {
        (q1["id"], q1["options"][0]["id"]),
        (q2["id"], q2["options"][1]["id"]),
    }

    # Second, partial save: change q1's answer, and don't mention q2 at all.
    second_payload = [{"question_id": q1["id"], "option_id": q1["options"][2]["id"]}]
    second_resp = client.put("/me/interest-answers", json=second_payload, headers=_auth(token))
    assert second_resp.status_code == 200

    rows = db_session.execute(select(InterestAnswer).where(InterestAnswer.user_id == user_id)).scalars().all()
    saved = {(row.question_id, row.chosen_option_id) for row in rows}
    # q1's answer was updated in place; q2's answer, omitted from the
    # second (partial) save, is still there -- a partial PUT merges into
    # what's already saved, it never drops an omitted question's answer.
    assert saved == {(q1["id"], q1["options"][2]["id"]), (q2["id"], q2["options"][1]["id"])}


def test_put_interest_answers_rejects_unknown_question_id(client, make_register_payload):
    _, token, _ = _register_and_login(client, make_register_payload)
    q1 = _first_two_questions_with_options(client, token)[0]

    resp = client.put(
        "/me/interest-answers",
        json=[{"question_id": 999999, "option_id": q1["options"][0]["id"]}],
        headers=_auth(token),
    )
    assert resp.status_code == 400


def test_put_interest_answers_rejects_unknown_option_id(client, make_register_payload):
    _, token, _ = _register_and_login(client, make_register_payload)
    q1 = _first_two_questions_with_options(client, token)[0]

    resp = client.put(
        "/me/interest-answers",
        json=[{"question_id": q1["id"], "option_id": 999999}],
        headers=_auth(token),
    )
    assert resp.status_code == 400


def test_put_interest_answers_rejects_option_from_another_question(client, make_register_payload):
    _, token, _ = _register_and_login(client, make_register_payload)
    q1, q2 = _first_two_questions_with_options(client, token)

    resp = client.put(
        "/me/interest-answers",
        # q1's question id paired with one of q2's option ids.
        json=[{"question_id": q1["id"], "option_id": q2["options"][0]["id"]}],
        headers=_auth(token),
    )
    assert resp.status_code == 400


def test_put_interest_answers_rejects_duplicate_question_in_payload(client, make_register_payload):
    _, token, _ = _register_and_login(client, make_register_payload)
    q1 = _first_two_questions_with_options(client, token)[0]

    resp = client.put(
        "/me/interest-answers",
        json=[
            {"question_id": q1["id"], "option_id": q1["options"][0]["id"]},
            {"question_id": q1["id"], "option_id": q1["options"][1]["id"]},
        ],
        headers=_auth(token),
    )
    assert resp.status_code == 400


def test_interest_answers_are_scoped_to_the_caller(client, make_register_payload, db_session):
    _, token_a, user_id_a = _register_and_login(client, make_register_payload)
    _, token_b, user_id_b = _register_and_login(client, make_register_payload)
    q1 = _first_two_questions_with_options(client, token_a)[0]

    resp_a = client.put(
        "/me/interest-answers",
        json=[{"question_id": q1["id"], "option_id": q1["options"][0]["id"]}],
        headers=_auth(token_a),
    )
    assert resp_a.status_code == 200

    # B retaking (even with no overlap) must never touch A's rows.
    resp_b = client.put("/me/interest-answers", json=[], headers=_auth(token_b))
    assert resp_b.status_code == 200

    rows_a = db_session.execute(select(InterestAnswer).where(InterestAnswer.user_id == user_id_a)).scalars().all()
    assert len(rows_a) == 1
    rows_b = db_session.execute(select(InterestAnswer).where(InterestAnswer.user_id == user_id_b)).scalars().all()
    assert len(rows_b) == 0


def test_interest_answers_require_auth(client):
    resp = client.put("/me/interest-answers", json=[])
    assert resp.status_code in (401, 403)


# --- GET /me/interest-answers (Phase 6: resume + completeness) --------------


def test_get_interest_answers_empty_when_none_saved(client, make_register_payload):
    _, token, _ = _register_and_login(client, make_register_payload)

    resp = client.get("/me/interest-answers", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json() == {"answers": [], "complete": False}


def test_get_interest_answers_resumes_a_partial_save(client, make_register_payload):
    _, token, _ = _register_and_login(client, make_register_payload)
    q1, q2 = _first_two_questions_with_options(client, token)

    payload = [
        {"question_id": q1["id"], "option_id": q1["options"][0]["id"]},
        {"question_id": q2["id"], "option_id": q2["options"][1]["id"]},
    ]
    put_resp = client.put("/me/interest-answers", json=payload, headers=_auth(token))
    assert put_resp.status_code == 200

    # A part-finished test (only 2 of 40 answered) must resume with exactly
    # those saved answers, and `complete` must be false.
    get_resp = client.get("/me/interest-answers", headers=_auth(token))
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["complete"] is False
    assert {(a["question_id"], a["option_id"]) for a in body["answers"]} == {
        (q1["id"], q1["options"][0]["id"]),
        (q2["id"], q2["options"][1]["id"]),
    }


def test_get_interest_answers_complete_once_all_40_answered(client, make_register_payload):
    _, token, _ = _register_and_login(client, make_register_payload)
    questions = _set_questions(client, token)
    assert len(questions) == 40

    # Answer 39 of 40 first -- still incomplete.
    partial_payload = [{"question_id": q["id"], "option_id": q["options"][0]["id"]} for q in questions[:39]]
    resp = client.put("/me/interest-answers", json=partial_payload, headers=_auth(token))
    assert resp.status_code == 200
    assert client.get("/me/interest-answers", headers=_auth(token)).json()["complete"] is False

    # Answer the last one -- now complete.
    last = questions[39]
    resp = client.put(
        "/me/interest-answers",
        json=[{"question_id": last["id"], "option_id": last["options"][0]["id"]}],
        headers=_auth(token),
    )
    assert resp.status_code == 200
    body = client.get("/me/interest-answers", headers=_auth(token)).json()
    assert body["complete"] is True
    assert len(body["answers"]) == 40


def test_interest_answers_progress_requires_auth(client):
    resp = client.get("/me/interest-answers")
    assert resp.status_code in (401, 403)


# --- DELETE /me cascades student input rows ---------------------------------


def test_delete_me_cascades_results_and_interest_answers(client, make_register_payload, db_session):
    _, token, user_id = _register_and_login(client, make_register_payload)
    q1 = _first_two_questions_with_options(client, token)[0]

    put_results = client.put(
        "/me/results",
        json=[{"subject_code": "BM", "grade": "A"}, {"subject_code": "SJ", "grade": "E"}],
        headers=_auth(token),
    )
    assert put_results.status_code == 200

    put_answers = client.put(
        "/me/interest-answers",
        json=[{"question_id": q1["id"], "option_id": q1["options"][0]["id"]}],
        headers=_auth(token),
    )
    assert put_answers.status_code == 200

    delete_resp = client.delete("/me", headers=_auth(token))
    assert delete_resp.status_code == 204

    remaining_results = db_session.execute(select(SPMResult).where(SPMResult.user_id == user_id)).scalars().all()
    remaining_answers = db_session.execute(
        select(InterestAnswer).where(InterestAnswer.user_id == user_id)
    ).scalars().all()
    assert remaining_results == []
    assert remaining_answers == []
