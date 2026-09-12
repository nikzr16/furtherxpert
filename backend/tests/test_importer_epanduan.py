"""Parser unit tests for `app.importer.epanduan` (plan Phase 3 task 3 check:
"Parser tests on saved real pages: UE4481001 (A and B), UP4481001 ('ATAU'),
and one Bumiputera-only program.").

Every fixture under `tests/fixtures/` is a real, unmodified response saved
from the live e-Panduan site while building this importer -- no live network
calls happen in this test module.
"""

from pathlib import Path

import pytest

from app.importer.epanduan import (
    DIPLOMA_CODE_RE,
    get_syarat_am_li_nodes,
    parse_general_requirement_html,
    parse_list_page,
    parse_program_requirement_html,
)
from app.importer.subjects import UnknownSubjectError, resolve_subject_name

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


# --- diploma code filter -------------------------------------------------


@pytest.mark.parametrize(
    "code,expected",
    [
        ("UE4481001", True),
        ("UP4481001", True),
        ("UA4111001", True),
        ("UY0000001", False),  # Asasi/foundation, not a diploma
        ("UH0010003", False),
    ],
)
def test_diploma_code_regex(code: str, expected: bool) -> None:
    assert bool(DIPLOMA_CODE_RE.match(code)) is expected


# --- list page parsing -----------------------------------------------------


class TestParseListPage:
    def setup_method(self) -> None:
        self.html = _fixture("list_A_page25.html")
        self.cards = {c.code: c for c in parse_list_page(self.html)}

    def test_ue4481001_card_fields(self) -> None:
        card = self.cards["UE4481001"]
        assert card.name == "DIPLOMA SAINS KOMPUTER"
        assert card.university_code == "UE"
        assert card.level == "Diploma"
        assert card.mode == "Konvensional"
        assert card.duration_value == 5
        assert card.duration_unit == "Semester"
        assert card.nec_code == "0613"
        assert card.nec_name == "Sains Komputer"
        assert card.interview is False
        assert card.avg_merit == pytest.approx(76.71)
        assert card.stem is True
        assert card.tvet is False
        assert card.bumiputera_badge is True
        assert "Kampus Arau, Perlis" in card.campuses
        assert len(card.career_paths) > 0

    def test_up4481001_card_fields(self) -> None:
        card = self.cards["UP4481001"]
        assert card.university_code == "UP"
        assert card.nec_code == "0613"
        assert card.campuses == ["Kampus Bintulu, Sarawak"]

    def test_every_diploma_card_has_a_code(self) -> None:
        diploma_cards = [c for c in self.cards.values() if DIPLOMA_CODE_RE.match(c.code)]
        assert diploma_cards  # the fixture page has at least one
        for card in diploma_cards:
            assert card.code
            assert card.name

    def test_syarat_am_general_requirement(self) -> None:
        li_nodes, text_ms = get_syarat_am_li_nodes(self.html, "UE4481001")
        result = parse_general_requirement_html(li_nodes, text_ms)
        assert result.unparsed is False
        assert result.rules["bumiputera_only"] is False
        assert result.rules["all"] == [
            {"subject": "BM", "min": "C"},
            {"subject": "SJ", "min": "E"},
            {"uncounted": 2, "min": "C"},
        ]


# --- syarat khas (program_requirements) parsing ----------------------------


class TestParseSyaratKhas:
    def test_ue4481001_bumiputera_and_one_of(self) -> None:
        """UE4481001 category A: single subjects + a one_of + an uncounted
        clause + the Bumiputera-only note (our required Bumiputera fixture)."""
        result = parse_program_requirement_html(_fixture("syaratkhas_A_UE4481001.html"))
        assert result.unparsed is False
        assert result.rules["bumiputera_only"] is True
        assert {"subject": "BI", "min": "C"} in result.rules["all"]
        assert {"subject": "MT", "min": "C"} in result.rules["all"]
        assert {"uncounted": 2, "min": "C"} in result.rules["all"]
        one_of_nodes = [n for n in result.rules["all"] if "one_of" in n]
        assert len(one_of_nodes) == 1
        assert one_of_nodes[0]["min"] == "C"
        assert one_of_nodes[0]["count"] == 1
        assert "MTT" in one_of_nodes[0]["one_of"]

    def test_ue4481001_category_b_matches_category_a(self) -> None:
        """UE4481001 category B: same rule set as A for this program (the
        proj-furtherxpert-rules skill notes A/B *can* differ per program, but
        here they happen to match -- this fixture is the required
        "UE4481001 (A and B)" check)."""
        result_b = parse_program_requirement_html(_fixture("syaratkhas_B_UE4481001.html"))
        result_a = parse_program_requirement_html(_fixture("syaratkhas_A_UE4481001.html"))
        assert result_b.unparsed is False
        assert result_b.rules["all"] == result_a.rules["all"]
        assert result_b.rules["bumiputera_only"] is True

    def test_up4481001_atau_branches(self) -> None:
        """UP4481001 category A: an explicit UPU "ATAU" (OR) between two
        alternative requirement branches."""
        result = parse_program_requirement_html(_fixture("syaratkhas_A_UP4481001.html"))
        assert result.unparsed is False
        assert result.rules["bumiputera_only"] is False
        assert len(result.rules["all"]) == 1
        any_node = result.rules["all"][0]
        assert "any" in any_node
        assert len(any_node["any"]) == 2
        branch1, branch2 = any_node["any"]
        assert {"subject": "BI", "min": "E"} in branch1["all"]
        assert any(n.get("one_of") == ["MTT"] for n in branch1["all"])
        assert any(n.get("one_of") == ["MT"] for n in branch2["all"])
        science_branch = next(n for n in branch2["all"] if n.get("one_of") != ["MT"])
        assert "SN" in science_branch["one_of"]
        assert "FZ" in science_branch["one_of"]

    def test_empty_ol_yields_no_rules(self) -> None:
        result = parse_program_requirement_html("<ol></ol>")
        assert result.rules["all"] == []
        assert result.unparsed is False

    def test_unrecognised_grade_clause_is_unparsed_not_guessed(self) -> None:
        html = "<ol><li>Mendapat sekurang-kurangnya Gred C dalam sesuatu yang pelik.</li></ol>"
        result = parse_program_requirement_html(html)
        assert result.unparsed is True
        assert result.rules["all"] == []  # never guessed a partial rule

    def test_unmapped_subject_name_raises(self) -> None:
        html = (
            "<ol><li>Mendapat sekurang-kurangnya Gred C dalam mata pelajaran "
            "Bahasa Yang Tidak Wujud.</li></ol>"
        )
        with pytest.raises(UnknownSubjectError):
            parse_program_requirement_html(html)


# --- subject resolution sanity (importer never guesses) --------------------


def test_resolve_subject_name_handles_case_and_period() -> None:
    assert resolve_subject_name("bahasa melayu") == "BM"
    assert resolve_subject_name("BAHASA MELAYU.") == "BM"


def test_resolve_subject_name_unknown_raises() -> None:
    with pytest.raises(UnknownSubjectError):
        resolve_subject_name("Not A Real Subject")


# --- encoding: no mojibake in parsed/stored text ----------------------------
#
# Regression test for the httpx charset-guessing bug (importer/epanduan.py
# `_request` now forces `resp.encoding = "utf-8"`): a wrong-charset decode of
# a real multi-byte UTF-8 character (e.g. the "•" bullet in a syarat khas
# subject table) previously turned it into "�" (U+FFFD REPLACEMENT
# CHARACTER, rendered as "�"). Every real fixture must parse/flatten to text
# with no such replacement character anywhere.


_SYARAT_KHAS_FIXTURES = [
    "syaratkhas_A_UE4481001.html",
    "syaratkhas_B_UE4481001.html",
    "syaratkhas_A_UP4481001.html",
]


@pytest.mark.parametrize("fixture_name", _SYARAT_KHAS_FIXTURES)
def test_parsed_text_ms_has_no_replacement_character(fixture_name: str) -> None:
    result = parse_program_requirement_html(_fixture(fixture_name))
    assert "�" not in result.text_ms


def test_ue4481001_bullet_survives_as_a_real_bullet_character() -> None:
    """The `&#8226;` entity in the subject table of syaratkhas_A_UE4481001.html
    must flatten to a real U+2022 bullet in `text_ms`, not a replacement
    character or a double-encoded mojibake sequence."""
    result = parse_program_requirement_html(_fixture("syaratkhas_A_UE4481001.html"))
    assert "•" in result.text_ms
    assert "�" not in result.text_ms


def test_list_page_parsed_fields_have_no_replacement_character() -> None:
    html = _fixture("list_A_page25.html")
    cards = parse_list_page(html)
    assert cards  # the fixture page has at least one card
    for card in cards:
        assert "�" not in card.name
        assert "�" not in card.syarat_am_text
        assert all("�" not in c for c in card.campuses)
        assert all("�" not in c for c in card.career_paths)

    li_nodes, am_text_ms = get_syarat_am_li_nodes(html, "UE4481001")
    assert "�" not in am_text_ms
    am_result = parse_general_requirement_html(li_nodes, am_text_ms)
    assert "�" not in am_result.text_ms
