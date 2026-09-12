"""Sequential e-Panduan fetcher + parser (plan Phase 3 task 3; proj-furtherxpert-rules
skill Section 4).

Reads the live UPUOnline e-Panduan site (https://online.mohe.gov.my/epanduan)
one page / one AJAX call at a time, keeps only UA diploma codes (``^U[A-Z]4``),
and turns the Malay "syarat am" / "syarat khas" text into the rule-tree shape
used by ``general_requirements.rules`` / ``program_requirements.rules``
(proj-furtherxpert-rules skill Section 3):

    {"subject": S, "min": G}
    {"one_of": [S...], "min": G, "count": n}
    {"uncounted": n, "min": G}
    {"any": [node...]}                       -- UPU "ATAU"
    {"all": [node...]}

Never guesses: an unmapped subject name raises ``UnknownSubjectError`` and
stops the run; a clause that doesn't match a known template is recorded in
``unparsed`` (whole program+category row, conservative) rather than silently
dropped or approximated. Clauses that are readable but not grade-checkable
(medical/age/portfolio notes, etc.) are collected in ``unverifiable`` instead.

Real site notes (found by probing the live site while building this importer
-- see the build report for the full trace):
  - The list endpoint needs a warmed-up session: a bare GET without first
    visiting ``/epanduan/`` (to pick up the Laravel session + XSRF cookies)
    returns HTTP 200 with an **empty body**. `EpanduanClient` always warms up
    first and reuses one cookie-carrying session for the whole run.
  - The list URL takes ``?jenprog=spm&page=N`` (not just ``?page=N``) --
    ``jenprog=spm`` selects the SPM-leaver path that categories A and B (UPU's
    "kategori calon") both live under.
  - Per-program detail blocks (``maklumatProgram__<CODE>``, ``kampus__<CODE>``,
    ``laluan-kerjaya_<CODE>``) are separate top-level modal ``<div>``s on the
    list page, not descendants of the program's ``.card.shop-list`` card --
    they're looked up by id, not by scoping into the card.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import time
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from selectolax.parser import HTMLParser, Node

from app.importer.reference_data import UNIVERSITIES
from app.importer.subjects import UnknownSubjectError, resolve_subject_name

logger = logging.getLogger(__name__)

# --- Site constants ---------------------------------------------------

BASE_URL = "https://online.mohe.gov.my/epanduan"
ENTRY_URL = f"{BASE_URL}/"
LIST_URL_TMPL = BASE_URL + "/ProgramPengajian/kategoriCalon/{category}"
SYARAT_KHAS_URL_TMPL = BASE_URL + "/ProgramPengajian/modalSyarat/{category}/{code}"

USER_AGENT = (
    "FurtherXpertAI-Importer/1.0 "
    "(+educational data aggregation for FurtherXpert; "
    "contact: nikzulfaqar678@gmail.com)"
)

# Politeness: one request in flight at a time, at least this many seconds
# between requests, retried with backoff on transient failures. Never call
# fetch_* concurrently.
REQUEST_DELAY_SECONDS = 1.0
MAX_RETRIES = 4
RETRY_BASE_SECONDS = 2.0
REQUEST_TIMEOUT_SECONDS = 30.0

# Sanity bounds confirmed against the live site (2026/2027 session run) --
# the crawler stops early per-category once a list page yields zero program
# cards, so this is a cap, not a hard requirement.
MAX_PAGES = {"A": 60, "B": 60}

# UA diploma codes only (plan Phase 3 task 3 / proj-furtherxpert-rules skill Sec 4).
DIPLOMA_CODE_RE = re.compile(r"^U[A-Z]4")

CATEGORIES = ("A", "B")


class ImporterError(Exception):
    """Raised for structural problems the importer refuses to guess through."""


# --- HTTP client --------------------------------------------------------


class EpanduanClient:
    """A polite, resumable, sequential HTTP client for e-Panduan.

    One shared ``httpx.Client`` (cookie jar persists across requests) is
    warmed up once against the entry page, then reused for every list page
    and every syarat-khas AJAX call. Every request is throttled to at most
    one per ``delay`` seconds and retried with exponential backoff on
    transient failures. Responses are cached to disk (``cache_dir``) so a
    re-run after an interruption doesn't re-fetch pages it already has.
    """

    def __init__(self, delay: float = REQUEST_DELAY_SECONDS, cache_dir: Path | None = None):
        self._client = httpx.Client(
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT_SECONDS,
            follow_redirects=True,
        )
        self._delay = delay
        self._last_request_at: float | None = None
        self._warmed_up = False
        self._cache_dir = cache_dir

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "EpanduanClient":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    # -- low level -------------------------------------------------------

    def _throttle(self) -> None:
        if self._last_request_at is not None:
            elapsed = time.monotonic() - self._last_request_at
            wait = self._delay - elapsed
            if wait > 0:
                time.sleep(wait)
        self._last_request_at = time.monotonic()

    def _request(self, url: str, *, headers: dict[str, str] | None = None) -> str:
        last_exc: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            self._throttle()
            try:
                resp = self._client.get(url, headers=headers)
            except httpx.HTTPError as exc:
                last_exc = exc
                logger.warning("Request error (attempt %d/%d) for %s: %s", attempt, MAX_RETRIES, url, exc)
                time.sleep(RETRY_BASE_SECONDS * (2 ** (attempt - 1)))
                continue
            if resp.status_code == 429 or resp.status_code >= 500:
                logger.warning(
                    "Transient HTTP %d (attempt %d/%d) for %s", resp.status_code, attempt, MAX_RETRIES, url
                )
                time.sleep(RETRY_BASE_SECONDS * (2 ** (attempt - 1)))
                continue
            resp.raise_for_status()
            # The site's list/AJAX responses are UTF-8 (confirmed by the
            # `<meta charset="utf-8">` on the entry/list pages), but the
            # AJAX fragments (`modalSyarat`) carry no charset of their own
            # and httpx falls back to guessing (chardet/charset_normalizer)
            # when the response has no explicit `charset=` in its
            # Content-Type header. That guess can be wrong, which silently
            # mangles any non-ASCII byte (e.g. a raw UTF-8 bullet/quote/dash)
            # into `�` on decode. Force UTF-8 explicitly rather than
            # trust the guess -- never re-decode with an assumed charset
            # elsewhere in this module.
            resp.encoding = "utf-8"
            text = resp.text
            if "�" in text:
                # Forced UTF-8 still couldn't decode every byte cleanly --
                # the upstream bytes themselves aren't UTF-8 for this
                # response. Don't silently store the mangled result.
                raise ImporterError(
                    f"Response for {url} contains invalid UTF-8 byte sequences "
                    "(decoded with U+FFFD replacement characters); refusing to "
                    "cache/parse it."
                )
            return text
        raise ImporterError(f"Failed to fetch {url} after {MAX_RETRIES} attempts") from last_exc

    def _cached(self, cache_key: str, fetch: "callable[[], str]") -> str:
        if self._cache_dir is None:
            return fetch()
        path = self._cache_dir / cache_key
        if path.exists():
            return path.read_text(encoding="utf-8")
        text = fetch()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return text

    def warm_up(self) -> None:
        """Visit the entry page once to pick up the Laravel session cookies.

        Without this, ``kategoriCalon`` and ``modalSyarat`` return HTTP 200
        with an empty body (verified against the live site).
        """
        if self._warmed_up:
            return
        self._cached("entry.html", lambda: self._request(ENTRY_URL))
        self._warmed_up = True

    # -- public fetchers ---------------------------------------------------

    def fetch_list_page(self, category: str, page: int) -> str:
        self.warm_up()
        url = f"{LIST_URL_TMPL.format(category=category)}?jenprog=spm&page={page}"
        referer = f"{BASE_URL}/kategoriCalon?jenprog=spm"
        return self._cached(
            f"list_{category}_p{page}.html",
            lambda: self._request(url, headers={"Referer": referer}),
        )

    def fetch_syarat_khas(self, category: str, code: str) -> str:
        self.warm_up()
        url = SYARAT_KHAS_URL_TMPL.format(category=category, code=code)
        return self._cached(
            f"syaratkhas_{category}_{code}.html",
            lambda: self._request(url, headers={"X-Requested-With": "XMLHttpRequest"}),
        )


# --- Parsed shapes --------------------------------------------------------


@dataclass
class ParsedListCard:
    code: str
    name: str
    university_code: str
    level: str | None
    mode: str | None
    duration_value: int | None
    duration_unit: str | None
    nec_code: str | None
    nec_name: str | None
    interview: bool
    avg_merit: float | None
    stem: bool
    tvet: bool
    bumiputera_badge: bool
    campuses: list[str] = field(default_factory=list)
    career_paths: list[str] = field(default_factory=list)
    syarat_am_text: str = ""


@dataclass
class RequirementResult:
    rules: dict[str, Any]
    text_ms: str
    unparsed: bool


# --- Text helpers ----------------------------------------------------------


def _clean(text: str) -> str:
    """Flatten parsed text for storage: normalise to NFC (so an accented
    Malay character or a bullet decoded via two different equivalent forms
    -- e.g. `&bull;` vs `&#8226;`, both U+2022 -- always ends up as the same
    single codepoint, never a "double-encoded" combining-character variant),
    then collapse all whitespace (including entity-derived `&nbsp;` /
    U+00A0) to single spaces.
    """
    text = unicodedata.normalize("NFC", text)
    return " ".join(text.split())


_COUNT_RE = re.compile(r"\((\d+)\)")


def _extract_count(text: str, default: int = 1) -> int:
    m = _COUNT_RE.search(text)
    return int(m.group(1)) if m else default


def _split_subject_names(raw: str) -> list[str]:
    """Split a "/"-joined e-Panduan cell like "Matematik / Matematik Tambahan"
    into individual raw subject name strings."""
    parts = [p.strip().rstrip(".") for p in raw.split("/")]
    return [p for p in parts if p]


def _resolve_subjects(raw_names: list[str]) -> list[str]:
    """resolve_subject_name() for each name; UnknownSubjectError propagates
    (never guessed/skipped, plan Phase 3 task 3)."""
    return [resolve_subject_name(name) for name in raw_names]


# --- syarat khas / syarat am item classification ----------------------------

_BUMIPUTERA_RE = re.compile(r"berketurunan melayu|bumiputera", re.IGNORECASE)

# "Mendapat sekurang-kurangnya Gred C dalam mata pelajaran Bahasa Inggeris."
_SINGLE_SUBJECT_RE = re.compile(
    r"Gred\s+([A-Za-z][+-]?)\s+(?:bagi|dalam)\s+mata\s*pelajaran\s+(.+)$",
    re.IGNORECASE,
)

# "Mendapat sekurang-kurangnya Gred E dalam SATU (1) mata pelajaran berikut :"
_ONE_OF_RE = re.compile(
    r"Gred\s+([A-Za-z][+-]?)\s+dalam\s+\S+\s*\(\d+\)\s+mata\s*pelajaran\s+berikut",
    re.IGNORECASE,
)

# "Mendapat sekurang-kurangnya Gred C dalam mana-mana DUA (2) mata pelajaran
#  yang belum diambil kira" (syarat khas phrasing) -- the trailing qualifier
# varies across real programs ("yang belum diambil kira", "yang belum
# dikira", "selain diatas", or nothing at all before the next clause), but
# "mana-mana <count>" always means the same "N subjects not otherwise used"
# clause; only a trailing "berikut" (a one_of table) means something else.
_UNCOUNTED_KHAS_RE = re.compile(
    r"Gred\s+([A-Za-z][+-]?)\s+dalam\s+mana-mana\s+\S+\s*\((\d+)\)\s+mata\s*pelajaran(?!\s+berikut)",
    re.IGNORECASE,
)

# "DUA (2) C dalam mana-mana matapelajaran yang belum dikira." (syarat am
# phrasing -- count-word-then-grade, no "Gred" keyword)
_UNCOUNTED_AM_RE = re.compile(
    r"\S+\s*\((\d+)\)\s+([A-Za-z][+-]?)\s+dalam\s+mana-mana\s+mata\s*pelajaran"
    r"\s+yang\s+belum\s+(?:diambil\s+kira|dikira)",
    re.IGNORECASE,
)

# Boilerplate lead-in lines that carry no grade-checkable content of their
# own (the real content is a nested <ol>/<li> sibling) -- safe to skip.
_BOILERPLATE_RE = re.compile(
    r"^warganegara malaysia|^memiliki\s.*:-$",
    re.IGNORECASE,
)


@dataclass
class _ItemOutcome:
    node: dict[str, Any] | None = None
    bumiputera: bool = False
    unverifiable: str | None = None
    unparsed: bool = False
    skip: bool = False


def _classify_item(item: Node) -> _ItemOutcome:
    """Classify one <li>/<div> requirement item into a rule node, a
    bumiputera flag, an unverifiable note, or "unparsed" (looked
    grade-related but didn't match a known template -- never guessed)."""
    table = item.css_first("table")
    raw_subjects: list[str] = []
    if table is not None:
        for tr in table.css("tr"):
            tds = tr.css("td")
            if not tds:
                continue
            raw_subjects.extend(_split_subject_names(tds[-1].text(strip=True)))
        table.decompose()

    sentence = _clean(item.text(strip=True, separator=" "))
    if not sentence and not raw_subjects:
        return _ItemOutcome(skip=True)

    if _BUMIPUTERA_RE.search(sentence):
        return _ItemOutcome(bumiputera=True)

    if _BOILERPLATE_RE.search(sentence):
        return _ItemOutcome(skip=True)

    m = _ONE_OF_RE.search(sentence)
    if m:
        grade = m.group(1).upper()
        count = _extract_count(sentence)
        if not raw_subjects:
            return _ItemOutcome(unparsed=True)
        subjects = _resolve_subjects(raw_subjects)
        return _ItemOutcome(node={"one_of": subjects, "min": grade, "count": count})

    m = _UNCOUNTED_KHAS_RE.search(sentence)
    if m:
        grade, count = m.group(1).upper(), int(m.group(2))
        return _ItemOutcome(node={"uncounted": count, "min": grade})

    m = _UNCOUNTED_AM_RE.search(sentence)
    if m:
        count, grade = int(m.group(1)), m.group(2).upper()
        return _ItemOutcome(node={"uncounted": count, "min": grade})

    m = _SINGLE_SUBJECT_RE.search(sentence)
    if m:
        grade = m.group(1).upper()
        raw_name = m.group(2).strip().rstrip(".")
        code = _resolve_subjects([raw_name])[0]
        return _ItemOutcome(node={"subject": code, "min": grade})

    # Doesn't match a known template. If it mentions a grade at all, this
    # could be a real requirement we're failing to parse -- never guess,
    # flag the whole row unparsed instead of silently dropping it.
    if re.search(r"\bGred\b", sentence, re.IGNORECASE) or _COUNT_RE.search(sentence):
        return _ItemOutcome(unparsed=True)

    # Readable, but not something the grade checker can verify (medical/age/
    # portfolio/etc. notes) -- proj-furtherxpert-rules skill Sec 3 `unverifiable`.
    return _ItemOutcome(unverifiable=sentence)


def _build_all_node(nodes: list[dict[str, Any]]) -> dict[str, Any]:
    if len(nodes) == 1:
        return nodes[0]
    return {"all": nodes}


def parse_program_requirement_html(html: str) -> RequirementResult:
    """Parse a `modalSyarat/{A|B}/{code}` AJAX fragment (syarat khas) into
    the rule-tree shape. ATAU (`<p><b>ATAU</b></p>`) splits the item stream
    into alternative branches, combined as `{"any": [...]}`.
    """
    tree = HTMLParser(html)
    text_ms = _clean(tree.body.text(strip=True, separator=" ")) if tree.body else _clean(html)
    root = tree.css_first("ol")
    if root is None:
        # No syarat khas beyond syarat am for this program+category.
        return RequirementResult(rules={"all": [], "bumiputera_only": False, "interview": False, "unverifiable": []}, text_ms=text_ms, unparsed=False)

    branches: list[list[dict[str, Any]]] = [[]]
    bumiputera_only = False
    unverifiable: list[str] = []
    unparsed = False

    for child in root.iter(include_text=False):
        tag = child.tag
        if tag == "p" and _clean(child.text(strip=True)).upper() == "ATAU":
            branches.append([])
            continue
        if tag not in ("li", "div"):
            continue
        # A stray <div><li>...</li></div> wrapper (seen around the
        # Bumiputera note): unwrap to the inner li if present.
        if tag == "div":
            inner_li = child.css_first("li")
            target = inner_li if inner_li is not None else child
        else:
            target = child
        outcome = _classify_item(target)
        if outcome.skip:
            continue
        if outcome.bumiputera:
            bumiputera_only = True
        elif outcome.unverifiable:
            unverifiable.append(outcome.unverifiable)
        elif outcome.unparsed:
            unparsed = True
        elif outcome.node:
            branches[-1].append(outcome.node)

    branches = [b for b in branches if b]
    all_nodes: list[dict[str, Any]] = []
    if len(branches) == 1:
        all_nodes.extend(branches[0])
    elif len(branches) > 1:
        all_nodes.append({"any": [_build_all_node(b) for b in branches]})

    rules = {
        "all": all_nodes,
        "bumiputera_only": bumiputera_only,
        "interview": False,  # filled in from maklumatProgram by the caller
        "unverifiable": unverifiable,
    }
    return RequirementResult(rules=rules, text_ms=text_ms, unparsed=unparsed)


def parse_general_requirement_html(li_nodes: list[Node], text_ms: str) -> RequirementResult:
    """Parse the syarat-am `<li>` items (already collected from the
    `#syarat-am-<CODE>` block) into the rule-tree shape. No ATAU has been
    observed in syarat am across the live snapshot; if one turns up the row
    is flagged unparsed rather than guessed at.
    """
    nodes: list[dict[str, Any]] = []
    bumiputera_only = False
    unverifiable: list[str] = []
    unparsed = False

    for li in li_nodes:
        outcome = _classify_item(li)
        if outcome.skip:
            continue
        if outcome.bumiputera:
            bumiputera_only = True
        elif outcome.unverifiable:
            unverifiable.append(outcome.unverifiable)
        elif outcome.unparsed:
            unparsed = True
        elif outcome.node:
            nodes.append(outcome.node)

    rules = {
        "all": nodes,
        "bumiputera_only": bumiputera_only,
        "interview": False,
        "unverifiable": unverifiable,
    }
    return RequirementResult(rules=rules, text_ms=text_ms, unparsed=unparsed)


# --- List page parsing -------------------------------------------------


def _parse_label_value_block(node: Node | None) -> dict[str, str]:
    """`maklumatProgram__<CODE>`'s fields are `<p class="para-desc ..."> Label
    : <b>Value</b> </p>` -- return {label: value}."""
    result: dict[str, str] = {}
    if node is None:
        return result
    for p in node.css("p.para-desc"):
        b = p.css_first("b")
        if b is None:
            continue
        value = _clean(b.text(strip=True, separator=" "))
        # Label is everything in the <p> before the <b>; drop trailing ':'.
        full = _clean(p.text(strip=True, separator=" "))
        label = full[: full.rfind(value)].strip() if value and value in full else full
        label = label.rstrip(":").strip()
        if label:
            result[label] = value
    return result


def _parse_kampus(node: Node | None) -> list[str]:
    if node is None:
        return []
    campuses = []
    for b in node.css("b.text-muted"):
        text = _clean(b.text(strip=True, separator=" ")).lstrip("-").strip()
        if text:
            campuses.append(text)
    return campuses


def _parse_laluan_kerjaya(node: Node | None) -> list[str]:
    if node is None:
        return []
    # Career names sit in one or more <b> tags inside the modal body; some
    # modals also have an earlier, empty <b> wrapping just a <br>, so collect
    # every non-empty one rather than taking the first match.
    texts = [_clean(b.text(strip=True, separator=" ")) for b in node.css("div.text-left b, p.text-muted b")]
    raw = ", ".join(t for t in texts if t)
    careers = [c.strip().rstrip(".") for c in raw.split(",")]
    return [c for c in careers if c]


def parse_list_page(html: str) -> list[ParsedListCard]:
    """Parse one `kategoriCalon/{A|B}?jenprog=spm&page=N` page into every
    program card on it (not yet filtered to UA diploma codes -- the caller
    filters by `DIPLOMA_CODE_RE`)."""
    tree = HTMLParser(html)
    cards = []
    for card in tree.css(".card.shop-list"):
        code_el = card.css_first(".executive-data-value")
        if code_el is None:
            continue
        code = _clean(code_el.text(strip=True))
        if not code:
            continue

        name_el = card.css_first("a.h5.fw-bold")
        name = _clean(name_el.text(strip=True, separator=" ")) if name_el else ""

        badge_classes: set[str] = set()
        for b in card.css(".executive-badges-container .badge"):
            badge_classes.update((b.attributes.get("class") or "").split())

        maklumat = tree.css_first(f"#maklumatProgram__{code}")
        fields = _parse_label_value_block(maklumat)

        level = fields.get("Peringkat Pengajian")
        mode = fields.get("Mod Pengajian")

        duration_value: int | None = None
        duration_unit: str | None = None
        duration_raw = fields.get("Tempoh Pengajian")
        if duration_raw:
            m = re.match(r"(\d+)\s*(\S+)", duration_raw)
            if m:
                duration_value, duration_unit = int(m.group(1)), m.group(2)

        nec_code: str | None = None
        nec_name: str | None = None
        nec_raw = fields.get("Bidang NEC")
        if nec_raw:
            m = re.match(r"(\d+)\s*(.*)$", nec_raw, re.DOTALL)
            if m:
                nec_code, nec_name = m.group(1), m.group(2).strip() or None

        interview = (fields.get("Bertemu duga / Ujian") or "").strip().lower() == "ya"

        avg_merit: float | None = None
        merit_raw = fields.get("Purata Markah Merit")
        if merit_raw:
            m = re.match(r"([\d.]+)", merit_raw)
            if m:
                avg_merit = float(m.group(1))

        kampus = tree.css_first(f"#kampus__{code}")
        laluan = tree.css_first(f"#laluan-kerjaya_{code}")
        syarat_am_el = tree.css_first(f"#syarat-am-{code}")
        syarat_am_text = (
            _clean(syarat_am_el.text(strip=True, separator=" ")) if syarat_am_el is not None else ""
        )

        cards.append(
            ParsedListCard(
                code=code,
                name=name,
                university_code=code[:2],
                level=level,
                mode=mode,
                duration_value=duration_value,
                duration_unit=duration_unit,
                nec_code=nec_code,
                nec_name=nec_name,
                interview=interview,
                avg_merit=avg_merit,
                stem="badge-stem" in badge_classes,
                tvet="badge-tvet" in badge_classes,
                bumiputera_badge="badge-bumi" in badge_classes,
                campuses=_parse_kampus(kampus),
                career_paths=_parse_laluan_kerjaya(laluan),
                syarat_am_text=syarat_am_text,
            )
        )
    return cards


def get_syarat_am_li_nodes(html: str, code: str) -> tuple[list[Node], str]:
    tree = HTMLParser(html)
    node = tree.css_first(f"#syarat-am-{code}")
    if node is None:
        return [], ""
    return node.css("li"), _clean(node.text(strip=True, separator=" "))


# --- Orchestration -------------------------------------------------------


@dataclass
class CategoryCoverage:
    total: int = 0
    fully_parsed: int = 0
    unparsed_examples: list[dict[str, str]] = field(default_factory=list)
    unverifiable_examples: list[dict[str, str]] = field(default_factory=list)


def run_import(
    *,
    session_name: str,
    latest_spm_year: int,
    delay: float = REQUEST_DELAY_SECONDS,
    cache_dir: Path | None = None,
    max_pages: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Run the full sequential import and return the snapshot dict written
    to `backend/data/upu/<session>.json`. Raises `UnknownSubjectError` (never
    guesses an unmapped subject name) or `ImporterError` on unrecoverable
    fetch failures.
    """
    max_pages = max_pages or MAX_PAGES
    client = EpanduanClient(delay=delay, cache_dir=cache_dir)

    programs_by_code: dict[str, dict[str, Any]] = {}
    general_requirements: dict[str, RequirementResult] = {}
    coverage = {"A": CategoryCoverage(), "B": CategoryCoverage()}
    unknown_universities: set[str] = set()

    try:
        client.warm_up()

        for category in CATEGORIES:
            am_texts_seen: set[str] = set()
            am_result: RequirementResult | None = None
            page = 1
            while page <= max_pages[category]:
                html = client.fetch_list_page(category, page)
                cards = parse_list_page(html)
                if not cards:
                    break

                for card in cards:
                    if not DIPLOMA_CODE_RE.match(card.code):
                        continue
                    if card.university_code not in UNIVERSITIES:
                        unknown_universities.add(card.university_code)

                    coverage[category].total += 1

                    li_nodes, am_text_ms = get_syarat_am_li_nodes(html, card.code)
                    if am_text_ms:
                        am_texts_seen.add(am_text_ms)
                        if am_result is None:
                            am_result = parse_general_requirement_html(li_nodes, am_text_ms)

                    khas_html = client.fetch_syarat_khas(category, card.code)
                    khas = parse_program_requirement_html(khas_html)
                    khas.rules["interview"] = card.interview

                    if khas.unparsed:
                        if len(coverage[category].unparsed_examples) < 3:
                            coverage[category].unparsed_examples.append(
                                {"code": card.code, "text": khas.text_ms[:400]}
                            )
                    else:
                        coverage[category].fully_parsed += 1
                    for note in khas.rules.get("unverifiable", []):
                        if len(coverage[category].unverifiable_examples) < 3:
                            coverage[category].unverifiable_examples.append({"code": card.code, "text": note})

                    entry = programs_by_code.setdefault(
                        card.code,
                        {
                            "code": card.code,
                            "university_code": card.university_code,
                            "requirements": {},
                        },
                    )
                    # Category A is the primary source for program-level
                    # facts (name, NEC, campuses, ...); category B only fills
                    # in gaps if the program wasn't seen in A (documented
                    # assumption -- see build report).
                    if category == "A" or "name" not in entry:
                        entry.update(
                            {
                                "name": card.name,
                                "nec_code": card.nec_code,
                                "nec_name": card.nec_name,
                                "level": card.level,
                                "mode": card.mode,
                                "duration_value": card.duration_value,
                                "duration_unit": card.duration_unit,
                                "avg_merit": card.avg_merit,
                                "stem": card.stem,
                                "tvet": card.tvet,
                                "campuses": card.campuses,
                                "career_paths": card.career_paths,
                            }
                        )
                    entry["interview"] = entry.get("interview", False) or card.interview
                    entry["bumiputera_only"] = (
                        entry.get("bumiputera_only", False) or card.bumiputera_badge or khas.rules["bumiputera_only"]
                    )
                    entry["requirements"][category] = {
                        "rules": khas.rules,
                        "text_ms": khas.text_ms,
                        "unparsed": khas.unparsed,
                    }

                    logger.info(
                        "%s %s: parsed (%s)", category, card.code, "unparsed" if khas.unparsed else "ok"
                    )

                page += 1

            if am_result is not None:
                general_requirements[category] = am_result
                if len(am_texts_seen) > 1:
                    logger.warning(
                        "Category %s: syarat am text was NOT identical across all diploma "
                        "programs (%d distinct variants seen) -- using the first one found; "
                        "review before trusting general_requirements[%s].",
                        category,
                        len(am_texts_seen),
                        category,
                    )
    finally:
        client.close()

    if unknown_universities:
        raise ImporterError(
            "Program codes with an unknown university prefix (not in "
            f"app/importer/reference_data.py UNIVERSITIES): {sorted(unknown_universities)}"
        )

    snapshot = {
        "session": {"name": session_name, "latest_spm_year": latest_spm_year},
        "general_requirements": {
            cat: {"rules": res.rules, "text_ms": res.text_ms, "unparsed": res.unparsed}
            for cat, res in general_requirements.items()
        },
        "programs": list(programs_by_code.values()),
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "coverage": {
                cat: {
                    "total": cov.total,
                    "fully_parsed": cov.fully_parsed,
                    "unparsed_examples": cov.unparsed_examples,
                    "unverifiable_examples": cov.unverifiable_examples,
                }
                for cat, cov in coverage.items()
            },
        },
    }
    return snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description="Import e-Panduan UA diploma reference data.")
    parser.add_argument("--session", default="2026/2027")
    parser.add_argument("--latest-spm-year", type=int, default=2025)
    parser.add_argument(
        "--out",
        default=str(Path(__file__).resolve().parents[2] / "data" / "upu" / "2026-2027.json"),
    )
    parser.add_argument("--delay", type=float, default=REQUEST_DELAY_SECONDS)
    parser.add_argument(
        "--cache-dir",
        default=str(Path(__file__).resolve().parents[2] / "data" / "upu" / ".cache"),
        help="Resume cache of raw HTML responses; delete to force a clean re-fetch.",
    )
    parser.add_argument("--no-cache", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    snapshot = run_import(
        session_name=args.session,
        latest_spm_year=args.latest_spm_year,
        delay=args.delay,
        cache_dir=None if args.no_cache else Path(args.cache_dir),
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False, sort_keys=False), encoding="utf-8")

    for cat, cov in snapshot["meta"]["coverage"].items():
        print(f"Category {cat}: {cov['fully_parsed']}/{cov['total']} programs fully parsed")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
