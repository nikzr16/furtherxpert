"""Why a Best Fit diploma is suggested (result explanations PRD T1-T2; plan
Processing Flow B).

Pure functions: plain data in, plain-words sentences out. No database, no
clock, no AI. The page only displays these sentences; it never builds its own
from numbers. Scores are rounded to 1 decimal, the same as the charts, so the
words always match the numbers on screen. Race is never mentioned: a
Bumiputera-only diploma only says the student qualifies (PRD section 6).
"""

from collections.abc import Sequence

# A short word for what a diploma teaches, by NEC field-of-study code. A
# 4-digit entry beats its 3-digit field. A code with no entry gets a sentence
# without a field word.
FIELD_WORDS: dict[str, str] = {
    "0412": "finance",
    "011": "teaching",
    "021": "arts and design",
    "022": "religious studies",
    "023": "language",
    "032": "media and communication",
    "041": "business",
    "042": "law",
    "051": "biology",
    "053": "physical science",
    "054": "mathematics",
    "061": "computing",
    "071": "engineering",
    "072": "manufacturing",
    "073": "architecture and building",
    "074": "engineering technology",
    "081": "agriculture",
    "082": "forestry",
    "083": "fisheries",
    "084": "veterinary",
    "091": "health",
    "101": "hospitality and tourism",
    "102": "occupational safety and health",
}

GENERAL_TITLE = "General UPU rules (syarat am)"
PROGRAM_TITLE = "This diploma's rules (syarat khas)"
NO_PROGRAM_RULES = "No extra subject rules beyond the general ones."
BUMIPUTERA_LINE = "Only open to Bumiputera students — you qualify."
ANY_LEAD = "You meet one of the allowed options:"
NOTHING_NEEDED = "Nothing else needed — no interview or test."
INTERVIEW_REASON = "Requires interview/test"
INTERVIEW_LINE = "You'll need to pass an interview or test."
UNVERIFIABLE_PREFIX = "Cannot verify automatically: "
SWEET_SPOT_LINE = (
    "That makes it a Sweet spot: it's in your top 3 for both what you're likely to excel in "
    "and what you're likely to love."
)
# Longer "one of" lists are summarised as a count; Program Detail shows the full rule text.
MAX_LISTED_OPTIONS = 5


def _pct(score: float) -> str:
    rounded = round(score, 1)
    return f"{int(rounded)}%" if rounded.is_integer() else f"{rounded}%"


def _article(word: str) -> str:
    return "an" if word[0].lower() in "aeiou" else "a"


def _and_join(items: Sequence[str]) -> str:
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def _field_word(nec_code: str) -> str | None:
    return FIELD_WORDS.get(nec_code[:4]) or FIELD_WORDS.get(nec_code[:3])


def _match_lines(program: dict, area: str, excel: dict | None, love: dict | None) -> list[str]:
    nec_code = program["nec_code"]
    field_name = f"{program['nec_name']} (code {nec_code})" if program.get("nec_name") else f"code {nec_code}"
    field = f"its field of study, {field_name}, is part of {area}."
    word = _field_word(nec_code)
    lines = [f"This is {_article(word)} {word} diploma: {field}" if word else field[0].upper() + field[1:]]

    if excel is not None:
        groups = _and_join([f"{name} ({_pct(score)})" for name, score in excel["groups"]])
        lines.append(
            f"{area} is #{excel['rank']} in what you're likely to excel in, at {_pct(excel['score'])}, "
            f"from your {groups} grades."
        )
    if love is not None:
        lines.append(
            f"{area} is #{love['rank']} in what you're likely to love, at {_pct(love['score'])}: "
            f"you picked {_article(area)} {area} answer in {love['picks']} of the {love['offered']} "
            "questions that offered one."
        )
    if excel is not None and love is not None:
        lines.append(SWEET_SPOT_LINE)
    return lines


def _leaf_line(node: dict, codes: list[str], grades: dict[str, str], names: dict[str, str]) -> str:
    def name(code: str) -> str:
        return names.get(code, code)

    chosen = ", ".join(f"{name(code)} ({grades[code]})" for code in codes)
    minimum = node["min"]

    if "subject" in node or ("one_of" in node and len(node["one_of"]) == 1):
        code = codes[0]
        return f"{name(code)} — needs {minimum}, you have {grades[code]}"
    if "one_of" in node:
        options = node["one_of"]
        count = node.get("count", 1)
        if len(options) <= MAX_LISTED_OPTIONS:
            listed = " / ".join(name(code) for code in options)
            return f"At least {minimum} in {count} of {listed} — {chosen}"
        return f"At least {minimum} in {count} of {len(options)} listed subjects — {chosen}"
    count = node["uncounted"]
    noun = "subject" if count == 1 else "subjects"
    return f"{count} more {noun} at {minimum} or better — {chosen}"


def _rule_sections(
    matching: list[dict] | None, grades: dict[str, str], names: dict[str, str], bumiputera_only: bool
) -> list[dict]:
    general: list[str] = []
    program: list[str] = []
    for entry in matching or []:
        lines = general if entry["side"] == "general" else program
        if "any" in entry["rule"] and len(entry["rule"]["any"]) > 1:
            lines.append(ANY_LEAD)
        lines.extend(_leaf_line(node, codes, grades, names) for node, codes in entry["parts"])
    if not program:
        program.append(NO_PROGRAM_RULES)
    if bumiputera_only:
        program.append(BUMIPUTERA_LINE)
    return [{"title": GENERAL_TITLE, "lines": general}, {"title": PROGRAM_TITLE, "lines": program}]


def _still_needed(verdict: str, reasons: list[str]) -> list[str]:
    if verdict == "Eligible":
        return [NOTHING_NEEDED]
    lines = []
    for reason in reasons:
        if reason == INTERVIEW_REASON:
            lines.append(INTERVIEW_LINE)
        elif reason.startswith(UNVERIFIABLE_PREFIX):
            lines.append(f"Check this yourself, as we can't confirm it from grades: {reason[len(UNVERIFIABLE_PREFIX):]}")
        else:
            lines.append(reason)
    return lines


def explain_program(
    *,
    program: dict,
    area: str,
    grades: dict[str, str],
    subject_names: dict[str, str],
    matching: list[dict] | None,
    bumiputera_only: bool,
    excel: dict | None,
    love: dict | None,
    position: int,
    total: int,
) -> dict:
    """The `why` object for one shown diploma (result explanations PRD T2).

    - `program`: needs `nec_code`, `nec_name`, `verdict`, `reasons`.
    - `matching`: from `eligibility.find_matching` on the same rules the
      checker used.
    - `excel`: `{"rank", "score", "groups": [(group name, score)]}` when the
      area is in Likely to excel, else None. `love`: `{"rank", "score",
      "picks", "offered"}` when it's in Likely to love, else None. Scores are
      full precision.
    - `position` / `total`: this diploma's place in the area's shown list, and
      how many Eligible + Conditional diplomas the area has.
    """
    noun = "diploma" if total == 1 else "diplomas"
    return {
        "match": _match_lines(program, area, excel, love),
        "rules": _rule_sections(matching, grades, subject_names, bumiputera_only),
        "still_needed": _still_needed(program["verdict"], program["reasons"]),
        "position": (
            f"{position} of {total} {noun} you can apply for in {area}. "
            "Eligible ones are shown first, then A to Z. See all of them on Explore."
        ),
    }
