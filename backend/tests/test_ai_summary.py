"""API tests for `GET /me/analysis/summary` and `app/services/ai_summary.py`
(PRD T4, T7; plan Phase 7 Check; skill `proj-auth-security` Section 5).

Every test here patches `app.services.ai_summary.OpenAI` so no test ever
makes a real network call. `fake_openai` (below) records each call's exact
keyword arguments so the privacy test can assert on what actually would
have left the process, not just on the code's stated intent.

Runs against the real, separate test database (see `tests/conftest.py`),
following the same request/response pattern as `tests/test_analysis.py`.
"""

import json
from types import SimpleNamespace

import pytest

from app.services import ai_summary


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


def _complete_results(client, token):
    """Enough SPM results that `subject_groups` (and therefore "not enough
    data") is non-empty -- BM/SJ are required on every save."""
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


def _complete_interest_test(client, token):
    """Answer all 20 questions with "None of the above" -- the test is
    complete (decision 0008), regardless of which areas end up scored."""
    questions = client.get("/interest-test").json()
    payload = []
    for q in questions:
        none_option = next(opt for opt in q["options"] if opt["text"] == "None of the above")
        payload.append({"question_id": q["id"], "option_id": none_option["id"]})
    resp = client.put("/me/interest-answers", json=payload, headers=_auth(token))
    assert resp.status_code == 200


def _complete_data(client, token):
    _complete_results(client, token)
    _complete_interest_test(client, token)


# --- Fake OpenAI client --------------------------------------------------


@pytest.fixture()
def fake_openai(monkeypatch):
    """Patches `app.services.ai_summary.OpenAI` with a call-recording fake.

    `fake_openai.calls` is a list of the exact `**kwargs` passed to
    `chat.completions.create(...)` on every call -- the real outgoing
    request shape, not the function's own intent.

    `fake_openai.configure(text=..., raise_exc=...)` controls what the next
    (and all following) calls do: return a canned reply, or raise.
    """
    calls: list[dict] = []
    state = {"text": "You show a good mix of strengths across a few subject areas. Keep exploring what interests you.", "raise_exc": None}

    class _FakeMessage:
        def __init__(self, content):
            self.content = content

    class _FakeChoice:
        def __init__(self, content):
            self.message = _FakeMessage(content)

    class _FakeResponse:
        def __init__(self, content):
            self.choices = [_FakeChoice(content)]

    class _FakeCompletions:
        def create(self, **kwargs):
            calls.append(kwargs)
            if state["raise_exc"] is not None:
                raise state["raise_exc"]
            return _FakeResponse(state["text"])

    class _FakeChat:
        def __init__(self):
            self.completions = _FakeCompletions()

    class _FakeOpenAI:
        def __init__(self, **kwargs):
            self.chat = _FakeChat()

    monkeypatch.setattr(ai_summary, "OpenAI", _FakeOpenAI)

    def _configure(text=None, raise_exc=None):
        if text is not None:
            state["text"] = text
        state["raise_exc"] = raise_exc

    return SimpleNamespace(calls=calls, configure=_configure)


# --- Privacy: the outgoing request carries no sensitive data -----------------


def test_ai_request_excludes_sensitive_fields(client, make_register_payload, fake_openai):
    payload, token, user_id = _register_and_login(client, make_register_payload, race="Melayu", is_citizen=True)
    _complete_data(client, token)

    resp = client.get("/me/analysis/summary", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["summary"] is not None

    assert len(fake_openai.calls) == 1
    call = fake_openai.calls[0]
    outgoing = json.dumps(call)
    # The actual student-specific data payload -- the "user" message -- is
    # the part built from student data at all; the "system" message is a
    # fixed instruction string that may legitimately *mention* words like
    # "citizenship" while telling the model it was never given any.
    user_message = next(m["content"] for m in call["messages"] if m["role"] == "user")

    # None of the following may ever appear anywhere in what was sent to
    # OpenAI, including the fixed system instructions.
    assert payload["email"] not in outgoing
    assert payload["race"] not in outgoing  # "Melayu"
    assert str(user_id) not in outgoing
    # Raw grade letters (e.g. "A+", the grade every subject was saved with)
    # never appear -- only the resulting subject-group percent scores do.
    assert "A+" not in outgoing

    # The actual data payload sent (not the fixed instructions) must carry
    # no citizenship, race, or program/eligibility data -- only area/group
    # names and scores (PRD T4).
    assert "citizen" not in user_message.lower()
    assert "eligib" not in user_message.lower()
    assert "race" not in user_message.lower()
    assert "program" not in user_message.lower()

    # Sanity check the payload is actually well-formed (area/group names +
    # scores), not empty -- an all-redacted empty payload would trivially
    # "pass" the assertions above without proving anything.
    assert "subject-group" in user_message.lower()
    assert "interest-area" in user_message.lower()


# --- Word limit: an over-long reply is truncated to <= 120 words -------------


def test_overlong_reply_is_truncated_to_120_words(client, make_register_payload, fake_openai):
    """The system prompt asks the model for <= 120 words, but a live check
    once got 122 words back anyway -- so `generate_summary` must enforce
    the cap itself, deterministically, regardless of what the model returns
    (plan Phase 7 hard requirement; PRD T4/T7 acceptance criteria)."""
    _, token, _ = _register_and_login(client, make_register_payload)
    _complete_data(client, token)

    filler = " ".join(f"word{i}" for i in range(150))
    assert len(filler.split()) == 150
    fake_openai.configure(text=filler)

    resp = client.get("/me/analysis/summary", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["summary"] is not None
    assert len(body["summary"].split()) <= 120


# --- AI failure never breaks /me/analysis, and /me/analysis/summary is friendly ---


def test_forced_ai_failure_still_returns_charts_and_friendly_summary(client, make_register_payload, fake_openai):
    _, token, _ = _register_and_login(client, make_register_payload)
    _complete_data(client, token)
    fake_openai.configure(raise_exc=RuntimeError("simulated OpenAI outage"))

    charts_resp = client.get("/me/analysis", headers=_auth(token))
    assert charts_resp.status_code == 200
    assert charts_resp.json()["subject_groups"] != []

    summary_resp = client.get("/me/analysis/summary", headers=_auth(token))
    assert summary_resp.status_code == 200
    body = summary_resp.json()
    assert body["status"] == "unavailable"
    assert body["summary"] is None
    assert body["message"]


def test_timeout_path_returns_friendly_null_not_500(client, make_register_payload, fake_openai):
    _, token, _ = _register_and_login(client, make_register_payload)
    _complete_data(client, token)
    fake_openai.configure(raise_exc=TimeoutError("simulated request timeout"))

    resp = client.get("/me/analysis/summary", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "unavailable"
    assert body["summary"] is None


# --- Caching: unchanged analysis is served from cache, a change regenerates ---


def test_cached_summary_reused_until_data_changes(client, make_register_payload, fake_openai):
    _, token, _ = _register_and_login(client, make_register_payload)
    _complete_data(client, token)

    first = client.get("/me/analysis/summary", headers=_auth(token))
    assert first.status_code == 200
    assert first.json()["status"] == "ok"
    assert len(fake_openai.calls) == 1

    # A second call for the same, unchanged analysis must be served from
    # cache -- the mocked OpenAI client must not be called again.
    second = client.get("/me/analysis/summary", headers=_auth(token))
    assert second.status_code == 200
    assert second.json()["summary"] == first.json()["summary"]
    assert len(fake_openai.calls) == 1

    # Changing SPM results invalidates the cached analysis (decision 0006),
    # which also drops the cached summary (see app/models/analysis.py) --
    # the next call must regenerate.
    _put_results(client, token, [{"subject_code": "BM", "grade": "D"}, {"subject_code": "SJ", "grade": "E"}])
    third = client.get("/me/analysis/summary", headers=_auth(token))
    assert third.status_code == 200
    assert third.json()["status"] == "ok"
    assert len(fake_openai.calls) == 2

    # Changing interest-test answers also invalidates it -- another regenerate.
    questions = client.get("/interest-test").json()
    q1 = questions[0]
    tagged_option = next(opt for opt in q1["options"] if opt["text"] != "None of the above")
    resp = client.put(
        "/me/interest-answers",
        json=[{"question_id": q1["id"], "option_id": tagged_option["id"]}],
        headers=_auth(token),
    )
    assert resp.status_code == 200
    fourth = client.get("/me/analysis/summary", headers=_auth(token))
    assert fourth.status_code == 200
    assert fourth.json()["status"] == "ok"
    assert len(fake_openai.calls) == 3


# --- Cross-user isolation -----------------------------------------------------


def test_cross_user_isolation(client, make_register_payload, fake_openai):
    _, token_a, _ = _register_and_login(client, make_register_payload)
    _, token_b, _ = _register_and_login(client, make_register_payload)

    # Only A finishes results + the interest test; B does neither.
    _complete_data(client, token_a)

    body_a = client.get("/me/analysis/summary", headers=_auth(token_a)).json()
    body_b = client.get("/me/analysis/summary", headers=_auth(token_b)).json()

    assert body_a["status"] == "ok"
    assert body_a["summary"] is not None
    # B's own (empty) data drives B's response -- never A's cached summary.
    assert body_b["status"] == "not_enough_data"
    assert body_b["summary"] is None

    # The AI was only ever called for A, once.
    assert len(fake_openai.calls) == 1


# --- Not enough data: the AI is never called --------------------------------


def test_not_enough_data_when_nothing_saved_yet(client, make_register_payload, fake_openai):
    _, token, _ = _register_and_login(client, make_register_payload)

    resp = client.get("/me/analysis/summary", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "not_enough_data"
    assert body["summary"] is None
    assert body["message"]
    assert fake_openai.calls == []


def test_not_enough_data_when_interest_test_incomplete(client, make_register_payload, fake_openai):
    _, token, _ = _register_and_login(client, make_register_payload)
    _complete_results(client, token)
    # Interest test left untouched -- 0 of 20 answered.

    resp = client.get("/me/analysis/summary", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "not_enough_data"
    assert fake_openai.calls == []


def test_not_enough_data_when_no_results_saved(client, make_register_payload, fake_openai):
    _, token, _ = _register_and_login(client, make_register_payload)
    _complete_interest_test(client, token)
    # No SPM results ever saved.

    resp = client.get("/me/analysis/summary", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "not_enough_data"
    assert fake_openai.calls == []


# --- Auth is required ----------------------------------------------------------


def test_analysis_summary_requires_auth(client):
    resp = client.get("/me/analysis/summary")
    assert resp.status_code in (401, 403)


def test_only_highlights_are_sent_to_the_ai():
    # Decision 0014: the model only ever sees the top 3 subject groups and the
    # top 3 non-zero interest areas, so it can't dwell on weak areas.
    from app.services.ai_summary import _build_user_message

    areas = [
        {"name": "Science & Technology", "score": 33.0},
        {"name": "Hospitality & Tourism", "score": 44.0},
        {"name": "Healthcare & Social Services", "score": 22.0},
        {"name": "Arts & Design", "score": 11.0},
        {"name": "Business & Management", "score": 0.0},
    ]
    groups = [
        {"name": "Mathematics", "score": 94.0},
        {"name": "Technical & ICT", "score": 89.0},
        {"name": "Languages", "score": 83.0},
        {"name": "Sciences", "score": 72.0},
        {"name": "Humanities", "score": 67.0},
    ]
    message = _build_user_message(areas, groups)

    for kept in ["Hospitality & Tourism", "Science & Technology", "Healthcare & Social Services",
                 "Mathematics", "Technical & ICT", "Languages"]:
        assert kept in message
    for dropped in ["Arts & Design", "Business & Management", "Sciences:", "Humanities"]:
        assert dropped not in message


def test_no_interest_highlights_when_all_zero():
    from app.services.ai_summary import _build_user_message

    message = _build_user_message(
        [{"name": "Arts & Design", "score": 0.0}], [{"name": "Mathematics", "score": 90.0}]
    )
    assert "Interest-area scores: none yet" in message
    assert "Arts & Design" not in message
