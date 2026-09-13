"""AI summary of a student's scores (PRD T4, T7; plan Phase 7 task 1; skill
`proj-auth-security` Section 5).

Builds a GPT-5 prompt from interest-area names + scores and subject-group
names + scores ONLY, then calls the OpenAI API with a hard timeout and no
retries. Deliberately impure (it makes an external network call), unlike
the fully pure `scoring.py` / `eligibility.py` -- but it still never touches
the database or the clock, and it never logs the prompt, the reply, or the
scores, not even on a failure path (proj-auth-security skill Section 5).

Privacy boundary (PDPA 2010, PRD T4): `generate_summary`'s two parameters
(`area_scores`, `group_scores`) are the entire boundary. Whatever is passed
in there is exactly what leaves this process toward OpenAI -- never email,
race, citizenship, raw grades, subject names paired with grades, a user id,
or program/eligibility data. The caller (`app/services/analysis.py`) is
responsible for only ever building those two lists from the already-scored
`GET /me/analysis` result, never from raw student rows.

This module never swallows a failure into an empty string -- a missing or
placeholder API key, a timeout, or any OpenAI API error is raised as
`AISummaryError`. The caller decides how to turn that into a friendly
`summary: null` response; that's not this module's job.
"""

from openai import OpenAI

from app.core.config import settings

# Well under the plan's Phase 7 Check ("under 10 seconds" end to end), so
# there's headroom left for the rest of the request/response cycle.
REQUEST_TIMEOUT_SECONDS = 6.0

# Roughly matches the ~120-word cap the prompt itself asks for; a hard
# ceiling so a runaway reply can't itself blow the time budget.
MAX_COMPLETION_TOKENS = 300

# The plan's Phase 7 hard requirement ("Keep it to 120 words or fewer") and
# the PRD's acceptance criteria. The system prompt below also asks the model
# to stay under this, but that's a request, not a guarantee -- a live check
# against the real OpenAI API once came back over (122 words), so
# `_enforce_word_limit` is the actual, deterministic enforcement.
MAX_SUMMARY_WORDS = 120

# `.env.example` ships `OPENAI_API_KEY=sk-changeme` as a placeholder. Treat
# that (or an empty key) as "no key configured" rather than sending a
# request to OpenAI that can only fail.
_PLACEHOLDER_KEYS = {"", "sk-changeme", "changeme"}

_SYSTEM_PROMPT = (
    "You write a short, plain-English summary of a Malaysian SPM student's "
    "self-assessment scores for a careers app. You are given two lists of "
    "scores only: subject-group strengths (0-100%) and interest-area "
    "scores (0-100%, from a self-report interest test). You are not given "
    "the student's name, grades, race, citizenship, or any program or "
    "eligibility data, and you must never invent or assume any of that. "
    "Write at most 120 words. Be encouraging but honest -- never exaggerate "
    "or invent an achievement. Never name a specific university, diploma "
    "program, or course, and never say or imply the student is 'eligible' "
    "or 'qualified' for anything -- you have no eligibility data at all. "
    "Only describe the strengths and interests the scores show. Focus on the "
    "student's top 2-3 subject strengths and top 2-3 interests, and what they "
    "could mean together. Leave out low or zero scores entirely: never list "
    "areas the student is not interested in, and never say they have 'no' "
    "or 'low' interest in anything. If there are no interest scores yet, talk "
    "only about subject strengths. Use a warm, supportive tone for a "
    "17-year-old."
)


class AISummaryError(Exception):
    """The AI summary could not be produced: a missing/placeholder API key,
    a timeout, or an OpenAI API error. Raised rather than swallowed, so the
    caller can decide how to present the failure to the student."""


def _is_configured(api_key: str) -> bool:
    return api_key not in _PLACEHOLDER_KEYS


def _enforce_word_limit(text: str) -> str:
    """Deterministically cap `text` at `MAX_SUMMARY_WORDS` words.

    Not just a tighter prompt -- the prompt already asks for this and once
    overshot it anyway, so this is the real guarantee. Prefers trimming to
    the last full sentence within the word budget (so the cut doesn't land
    mid-sentence); falls back to a plain word-count cut if no sentence
    boundary is found in the truncated text.
    """
    words = text.split()
    if len(words) <= MAX_SUMMARY_WORDS:
        return text

    truncated = " ".join(words[:MAX_SUMMARY_WORDS])
    last_sentence_end = max(truncated.rfind(ch) for ch in ".!?")
    if last_sentence_end != -1:
        return truncated[: last_sentence_end + 1]
    return truncated


# Only the student's highlights reach the model (decision 0014): the prompt
# alone didn't stop it listing weak or zero-score areas, so low scores are
# simply never sent.
HIGHLIGHT_COUNT = 3


def _highlights(scores: list[dict], *, drop_zero: bool) -> list[dict]:
    kept = [s for s in scores if not (drop_zero and s["score"] <= 0)]
    return sorted(kept, key=lambda s: (-s["score"], s["name"]))[:HIGHLIGHT_COUNT]


def _build_user_message(area_scores: list[dict], group_scores: list[dict]) -> str:
    top_areas = _highlights(area_scores, drop_zero=True)
    top_groups = _highlights(group_scores, drop_zero=False)
    area_line = ", ".join(f"{a['name']}: {a['score']:.0f}%" for a in top_areas) or "none yet"
    group_line = ", ".join(f"{g['name']}: {g['score']:.0f}%" for g in top_groups) or "none yet"
    return f"Interest-area scores: {area_line}\nSubject-group scores: {group_line}"


def generate_summary(area_scores: list[dict], group_scores: list[dict]) -> str:
    """Return a plain-English summary of the given scores (PRD T4, T7).

    `area_scores` / `group_scores`: `[{"name": str, "score": float}, ...]`
    -- interest-area and subject-group names and scores ONLY. These two
    parameters are the whole privacy boundary (see module docstring).

    Raises `AISummaryError` on a missing/placeholder key, a timeout, or any
    other OpenAI API error.
    """
    if not _is_configured(settings.OPENAI_API_KEY):
        raise AISummaryError("OPENAI_API_KEY is not configured")

    client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=REQUEST_TIMEOUT_SECONDS, max_retries=0)
    user_message = _build_user_message(area_scores, group_scores)

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            max_completion_tokens=MAX_COMPLETION_TOKENS,
            reasoning_effort="minimal",
            verbosity="low",
        )
    except Exception as exc:
        # Broad on purpose: any OpenAI SDK error (OpenAIError and its
        # subclasses, e.g. APITimeoutError) or any other transport-level
        # failure a test simulates must become an AISummaryError, never
        # propagate as a raw exception the caller has to know the shape of.
        raise AISummaryError("OpenAI request failed") from exc

    text = response.choices[0].message.content if response.choices else None
    if not text or not text.strip():
        raise AISummaryError("OpenAI returned an empty reply")
    return _enforce_word_limit(text.strip())
