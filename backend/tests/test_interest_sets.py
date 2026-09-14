"""API tests for interest test sets and rotation (rotation PRD criteria 5-8
and 10; rotation plan Testing Strategy "API"):
`GET /me/interest-test`, `POST /me/interest-test/rotate`, and how
`PUT /me/interest-answers` / `GET /me/analysis` behave with sets.

Runs against the real, separate test database (see `tests/conftest.py`).
"""

import uuid

from sqlalchemy import func, select

from app.models.interest_test import InterestAnswer, InterestQuestion, InterestTestSet, InterestTestSetQuestion

NONE = "None of the above"


def _register_and_login(client, make_register_payload, **overrides):
    payload = make_register_payload(**overrides)
    register_response = client.post("/auth/register", json=payload)
    assert register_response.status_code == 201
    login_response = client.post("/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert login_response.status_code == 200
    return login_response.json()["access_token"], uuid.UUID(register_response.json()["id"])


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _open(client, token) -> dict:
    resp = client.get("/me/interest-test", headers=_auth(token))
    assert resp.status_code == 200, resp.text
    return resp.json()


def _option(question: dict, tagged: bool) -> dict:
    return next(opt for opt in question["options"] if (opt["text"] != NONE) == tagged)


def _finish(client, token, body: dict, tag_first: bool = True) -> None:
    """Answer every question in the set: the first one with an area-tagged
    answer (if `tag_first`), the rest "None of the above"."""
    payload = [
        {"question_id": q["id"], "option_id": _option(q, tagged=tag_first and i == 0)["id"]}
        for i, q in enumerate(body["questions"])
    ]
    resp = client.put("/me/interest-answers", json=payload, headers=_auth(token))
    assert resp.status_code == 200, resp.text


def _question_ids(body: dict) -> list[int]:
    return [q["id"] for q in body["questions"]]


def test_first_open_creates_a_40_question_set_with_no_area_leak(client, make_register_payload):
    token, _ = _register_and_login(client, make_register_payload)
    body = _open(client, token)

    assert body["total"] == 40
    assert len(set(_question_ids(body))) == 40
    assert body["answers"] == []
    assert body["answered"] == 0
    assert body["complete"] is False
    assert body["has_finished_set"] is False
    for question in body["questions"]:
        assert set(question.keys()) == {"id", "text", "options"}
        # 4 tagged answers + "None of the above".
        assert len(question["options"]) == 5
        for option in question["options"]:
            assert set(option.keys()) == {"id", "text"}
        assert any(option["text"] == NONE for option in question["options"])


def test_opening_twice_reuses_one_set(client, make_register_payload, db_session):
    token, user_id = _register_and_login(client, make_register_payload)
    first = _open(client, token)
    second = _open(client, token)

    assert second["set_id"] == first["set_id"]
    count = db_session.execute(
        select(func.count()).select_from(InterestTestSet).where(InterestTestSet.user_id == user_id)
    ).scalar_one()
    assert count == 1


def test_reopening_an_unfinished_set_resumes_the_same_questions_order_and_answers(client, make_register_payload):
    token, _ = _register_and_login(client, make_register_payload)
    first = _open(client, token)
    q1, q2 = first["questions"][:2]
    saved = [
        {"question_id": q1["id"], "option_id": _option(q1, tagged=True)["id"]},
        {"question_id": q2["id"], "option_id": _option(q2, tagged=False)["id"]},
    ]
    assert client.put("/me/interest-answers", json=saved, headers=_auth(token)).status_code == 200

    again = _open(client, token)
    assert again["set_id"] == first["set_id"]
    assert _question_ids(again) == _question_ids(first)
    assert {(a["question_id"], a["option_id"]) for a in again["answers"]} == {
        (a["question_id"], a["option_id"]) for a in saved
    }
    assert again["answered"] == 2
    assert again["complete"] is False


def test_get_interest_answers_never_creates_a_set(client, make_register_payload, db_session):
    token, user_id = _register_and_login(client, make_register_payload)

    resp = client.get("/me/interest-answers", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json() == {"answers": [], "complete": False}
    count = db_session.execute(
        select(func.count()).select_from(InterestTestSet).where(InterestTestSet.user_id == user_id)
    ).scalar_one()
    assert count == 0


def test_finishing_then_reopening_gives_a_new_set_and_keeps_the_results(client, make_register_payload):
    token, _ = _register_and_login(client, make_register_payload)
    first = _open(client, token)
    _finish(client, token, first)

    assert client.get("/me/interest-answers", headers=_auth(token)).json()["complete"] is True
    results_before = client.get("/me/analysis", headers=_auth(token)).json()
    assert results_before["interest_test_complete"] is True
    assert len(results_before["likely_to_love"]) == 1

    second = _open(client, token)
    assert second["set_id"] != first["set_id"]
    assert second["answered"] == 0
    assert second["has_finished_set"] is True
    assert not set(_question_ids(first)) & set(_question_ids(second))

    results_after = client.get("/me/analysis", headers=_auth(token)).json()
    assert results_after["interest_test_complete"] is True
    assert results_after["interest_areas"] == results_before["interest_areas"]
    assert results_after["likely_to_love"] == results_before["likely_to_love"]


def test_rotate_discards_the_unfinished_sets_answers_and_gives_fresh_questions(
    client, make_register_payload, db_session
):
    token, _ = _register_and_login(client, make_register_payload)
    first = _open(client, token)
    payload = [{"question_id": q["id"], "option_id": _option(q, tagged=True)["id"]} for q in first["questions"][:3]]
    assert client.put("/me/interest-answers", json=payload, headers=_auth(token)).status_code == 200

    resp = client.post("/me/interest-test/rotate", headers=_auth(token))
    assert resp.status_code == 200
    rotated = resp.json()
    assert rotated["set_id"] != first["set_id"]
    assert rotated["total"] == 40
    assert rotated["answered"] == 0
    assert not set(_question_ids(first)) & set(_question_ids(rotated))

    old_set = db_session.get(InterestTestSet, first["set_id"])
    assert old_set.discarded_at is not None
    old_answers = db_session.execute(
        select(func.count()).select_from(InterestAnswer).where(InterestAnswer.set_id == first["set_id"])
    ).scalar_one()
    assert old_answers == 0
    # The rotated-away set's question list stays, as "seen" history.
    kept_questions = db_session.execute(
        select(func.count())
        .select_from(InterestTestSetQuestion)
        .where(InterestTestSetQuestion.set_id == first["set_id"])
    ).scalar_one()
    assert kept_questions == 40

    assert _open(client, token)["set_id"] == rotated["set_id"]


def test_rotate_does_not_touch_a_finished_sets_results(client, make_register_payload):
    token, _ = _register_and_login(client, make_register_payload)
    _finish(client, token, _open(client, token))
    results_before = client.get("/me/analysis", headers=_auth(token)).json()

    second = _open(client, token)
    q = second["questions"][0]
    client.put(
        "/me/interest-answers",
        json=[{"question_id": q["id"], "option_id": _option(q, tagged=True)["id"]}],
        headers=_auth(token),
    )
    rotated = client.post("/me/interest-test/rotate", headers=_auth(token)).json()
    assert rotated["has_finished_set"] is True

    results_after = client.get("/me/analysis", headers=_auth(token)).json()
    assert results_after["interest_test_complete"] is True
    assert results_after["interest_areas"] == results_before["interest_areas"]


def test_answer_for_a_question_outside_the_current_set_is_rejected(client, make_register_payload, db_session):
    token, _ = _register_and_login(client, make_register_payload)
    body = _open(client, token)
    outside = db_session.execute(
        select(InterestQuestion).where(InterestQuestion.id.notin_(_question_ids(body))).limit(1)
    ).scalar_one()

    resp = client.put(
        "/me/interest-answers",
        json=[{"question_id": outside.id, "option_id": outside.options[0].id}],
        headers=_auth(token),
    )
    assert resp.status_code == 400


def test_answering_before_any_set_exists_is_rejected(client, make_register_payload, db_session):
    token, _ = _register_and_login(client, make_register_payload)
    question = db_session.execute(select(InterestQuestion).limit(1)).scalar_one()

    resp = client.put(
        "/me/interest-answers",
        json=[{"question_id": question.id, "option_id": question.options[0].id}],
        headers=_auth(token),
    )
    assert resp.status_code == 400


def test_finishing_a_second_set_deletes_the_first_sets_answers(client, make_register_payload, db_session):
    token, user_id = _register_and_login(client, make_register_payload)
    first = _open(client, token)
    _finish(client, token, first)
    second = _open(client, token)
    _finish(client, token, second, tag_first=False)

    set_ids = set(
        db_session.execute(select(InterestAnswer.set_id).where(InterestAnswer.user_id == user_id)).scalars()
    )
    assert set_ids == {second["set_id"]}
    # The newest finished set now feeds My Results: all "None of the above".
    results = client.get("/me/analysis", headers=_auth(token)).json()
    assert results["interest_test_complete"] is True
    assert results["likely_to_love"] == []


def test_one_students_rotation_never_touches_another_students_set(client, make_register_payload):
    token_a, _ = _register_and_login(client, make_register_payload)
    token_b, _ = _register_and_login(client, make_register_payload)
    set_a = _open(client, token_a)
    q = set_a["questions"][0]
    saved = {"question_id": q["id"], "option_id": _option(q, tagged=True)["id"]}
    assert client.put("/me/interest-answers", json=[saved], headers=_auth(token_a)).status_code == 200

    set_b = _open(client, token_b)
    assert set_b["set_id"] != set_a["set_id"]
    assert set_b["answers"] == []
    client.post("/me/interest-test/rotate", headers=_auth(token_b))

    again_a = _open(client, token_a)
    assert again_a["set_id"] == set_a["set_id"]
    assert again_a["answers"] == [saved]


def test_delete_me_removes_sets_and_answers(client, make_register_payload, db_session):
    token, user_id = _register_and_login(client, make_register_payload)
    body = _open(client, token)
    q = body["questions"][0]
    client.put(
        "/me/interest-answers",
        json=[{"question_id": q["id"], "option_id": q["options"][0]["id"]}],
        headers=_auth(token),
    )

    assert client.delete("/me", headers=_auth(token)).status_code == 204

    assert db_session.execute(select(InterestTestSet).where(InterestTestSet.user_id == user_id)).all() == []
    assert (
        db_session.execute(select(InterestTestSetQuestion).where(InterestTestSetQuestion.set_id == body["set_id"])).all()
        == []
    )
    assert db_session.execute(select(InterestAnswer).where(InterestAnswer.user_id == user_id)).all() == []


def test_set_routes_require_auth(client):
    assert client.get("/me/interest-test").status_code in (401, 403)
    assert client.post("/me/interest-test/rotate").status_code in (401, 403)


def test_public_fixed_question_list_is_gone(client):
    assert client.get("/interest-test").status_code == 404
