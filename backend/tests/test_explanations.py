"""Unit tests for `app/services/explanations.py` ("Why this diploma?";
result explanations plan Step 10.1 task 6). Pure: no database.

Every expected sentence is written out by hand from the PRD wording and the
inputs, never copied from the code's output.
"""

from app.services.eligibility import find_matching
from app.services.explanations import explain_program

NAMES = {
    "BM": "Bahasa Melayu",
    "SJ": "Sejarah",
    "BI": "Bahasa Inggeris",
    "MT": "Matematik",
    "FZ": "Fizik",
    "KM": "Kimia",
    "BL": "Biologi",
    "EK": "Ekonomi",
    "GG": "Geografi",
}
GENERAL = {"all": [{"min": "C", "subject": "BM"}, {"min": "E", "subject": "SJ"}, {"min": "C", "uncounted": 2}]}


def _explain(program, program_rules, grades, *, area="Business & Management", excel=None, love=None,
             bumiputera_only=False, position=1, total=3):
    return explain_program(
        program=program,
        area=area,
        grades=grades,
        subject_names=NAMES,
        matching=find_matching(GENERAL, program_rules, grades),
        bumiputera_only=bumiputera_only,
        excel=excel,
        love=love,
        position=position,
        total=total,
    )


def _program(nec_code, nec_name, verdict="Eligible", reasons=None):
    return {"nec_code": nec_code, "nec_name": nec_name, "verdict": verdict, "reasons": reasons or []}


def test_excel_only_finance_diploma_with_no_extra_rules():
    grades = {"BM": "A", "SJ": "B", "MT": "A", "EK": "A-", "GG": "C"}
    why = _explain(
        _program("0412", "Kewangan, Perbankan Dan Insurans"),
        {"all": []},
        grades,
        excel={"rank": 2, "score": (8 / 9 * 100 + 7 / 9 * 100) / 2, "groups": [("Mathematics", 8 / 9 * 100), ("Commerce", 7 / 9 * 100)]},
        position=1,
        total=9,
    )

    assert why["match"] == [
        "This is a finance diploma: its field of study, Kewangan, Perbankan Dan Insurans (code 0412), "
        "is part of Business & Management.",
        "Business & Management is #2 in what you're likely to excel in, at 83.3%, "
        "from your Mathematics (88.9%) and Commerce (77.8%) grades.",
    ]
    assert why["rules"] == [
        {
            "title": "General UPU rules (syarat am)",
            "lines": [
                "Bahasa Melayu — needs C, you have A",
                "Sejarah — needs E, you have B",
                # Left after BM and SJ: MT A, EK A-, GG C -> MT, EK.
                "2 more subjects at C or better — Matematik (A), Ekonomi (A-)",
            ],
        },
        {"title": "This diploma's rules (syarat khas)", "lines": ["No extra subject rules beyond the general ones."]},
    ]
    assert why["still_needed"] == ["Nothing else needed — no interview or test."]
    assert why["position"] == (
        "1 of 9 diplomas you can apply for in Business & Management. "
        "Eligible ones are shown first, then A to Z. See all of them on Explore."
    )


def test_love_only_health_diploma():
    grades = {"BM": "B", "SJ": "C", "BI": "B", "EK": "C"}
    why = _explain(
        _program("0913", "Kejururawatan, Perbidanan Dan Pembantu Perubatan"),
        {"all": []},
        grades,
        area="Healthcare & Social Services",
        love={"rank": 1, "score": 9 / 17 * 100, "picks": 9, "offered": 17},
    )
    assert why["match"] == [
        "This is a health diploma: its field of study, Kejururawatan, Perbidanan Dan Pembantu Perubatan (code 0913), "
        "is part of Healthcare & Social Services.",
        "Healthcare & Social Services is #1 in what you're likely to love, at 52.9%: "
        "you picked a Healthcare & Social Services answer in 9 of the 17 questions that offered one.",
    ]


def test_sweet_spot_engineering_diploma_uses_an_and_whole_percentages():
    grades = {"BM": "A+", "SJ": "A", "MT": "A+", "FZ": "A+", "KM": "A", "BL": "A"}
    why = _explain(
        _program("0713", "Kuasa Elektrik Dan Tenaga"),
        {"all": []},
        grades,
        area="Science & Technology",
        excel={"rank": 1, "score": 100.0, "groups": [("Mathematics", 100.0)]},
        love={"rank": 3, "score": 50.0, "picks": 9, "offered": 18},
    )
    assert why["match"] == [
        "This is an engineering diploma: its field of study, Kuasa Elektrik Dan Tenaga (code 0713), "
        "is part of Science & Technology.",
        "Science & Technology is #1 in what you're likely to excel in, at 100%, from your Mathematics (100%) grades.",
        "Science & Technology is #3 in what you're likely to love, at 50%: "
        "you picked a Science & Technology answer in 9 of the 18 questions that offered one.",
        "That makes it a Sweet spot: it's in your top 3 for both what you're likely to excel in "
        "and what you're likely to love.",
    ]


def test_no_field_word_and_an_area_starting_with_a_vowel():
    why = _explain(
        _program("0888", "Program Dan Kelayakan Antara-Disiplin"),
        {"all": []},
        {"BM": "A", "SJ": "A", "BL": "A", "KM": "A"},
        area="Agriculture & Environment",
        love={"rank": 2, "score": 25.0, "picks": 4, "offered": 16},
    )
    assert why["match"] == [
        "Its field of study, Program Dan Kelayakan Antara-Disiplin (code 0888), is part of Agriculture & Environment.",
        "Agriculture & Environment is #2 in what you're likely to love, at 25%: "
        "you picked an Agriculture & Environment answer in 4 of the 16 questions that offered one.",
    ]


def test_one_option_rule_reads_like_a_subject_rule_and_lists_short_options():
    program_rules = {
        "all": [
            {"min": "C", "count": 1, "one_of": ["BI"]},
            {"min": "C", "count": 1, "one_of": ["FZ", "KM", "BL"]},
            {
                "any": [
                    {"all": [{"min": "E", "subject": "EK"}, {"min": "C", "count": 1, "one_of": ["MT"]}]},
                    {"min": "A", "subject": "GG"},
                ]
            },
        ],
        "bumiputera_only": True,
    }
    grades = {"BM": "A", "SJ": "C", "BI": "B", "MT": "B", "FZ": "B", "KM": "A", "EK": "D", "GG": "B", "BL": "C"}
    why = _explain(
        _program("0511", "Biologi"),
        program_rules,
        grades,
        area="Science & Technology",
        excel={"rank": 3, "score": 70.0, "groups": [("Sciences", 70.0)]},
        bumiputera_only=True,
    )
    # Named rules in order: BM, SJ, BI, (FZ/KM/BL -> KM A), any -> first branch:
    # EK D meets E, MT B meets C. Then "2 more": left FZ B, GG B, BL C -> FZ, GG.
    assert why["rules"] == [
        {
            "title": "General UPU rules (syarat am)",
            "lines": [
                "Bahasa Melayu — needs C, you have A",
                "Sejarah — needs E, you have C",
                "2 more subjects at C or better — Fizik (B), Geografi (B)",
            ],
        },
        {
            "title": "This diploma's rules (syarat khas)",
            "lines": [
                "Bahasa Inggeris — needs C, you have B",
                "At least C in 1 of Fizik / Kimia / Biologi — Kimia (A)",
                "You meet one of the allowed options:",
                "Ekonomi — needs E, you have D",
                "Matematik — needs C, you have B",
                "Only open to Bumiputera students — you qualify.",
            ],
        },
    ]


def test_long_option_lists_are_summarised_as_a_count():
    options = ["MTT", "FZ", "KM", "BL", "SNT", "SN", "SK"]
    why = _explain(
        _program("0613", "Sains Komputer"),
        {"all": [{"min": "C", "count": 1, "one_of": options}]},
        {"BM": "A", "SJ": "A", "FZ": "A+", "EK": "B", "GG": "B"},
        area="Science & Technology",
        excel={"rank": 1, "score": 90.0, "groups": [("Sciences", 90.0)]},
    )
    assert why["rules"][1]["lines"] == ["At least C in 1 of 7 listed subjects — Fizik (A+)"]


def test_conditional_diploma_says_what_is_still_needed():
    program = _program(
        "0211",
        "Teknik Audio-Visual Dan Penerbitan Media",
        verdict="Conditional",
        reasons=["Requires interview/test", "Cannot verify automatically: Tidak rabun warna."],
    )
    why = _explain(program, {"all": []}, {"BM": "C", "SJ": "D", "BI": "C", "EK": "C"}, area="Arts & Design",
                   love={"rank": 1, "score": 20.0, "picks": 3, "offered": 15}, position=1, total=1)
    assert why["still_needed"] == [
        "You'll need to pass an interview or test.",
        "Check this yourself, as we can't confirm it from grades: Tidak rabun warna.",
    ]
    assert why["position"].startswith("1 of 1 diploma you can apply for in Arts & Design.")
