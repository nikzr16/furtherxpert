"""Static reference data the importer seeds alongside the yearly snapshot:
university codes -> names, and the interest-area mapping (PRD T1).

Both are small, hand-maintained lists (not scraped) -- university codes are
given by the build task; the area mapping is PRD T1's table verbatim, kept
here as one source of truth for the importer and the data migration.
"""

from dataclasses import dataclass, field

# University code -> name, from the build task (also confirmed against
# e-Panduan program cards during the live import run).
UNIVERSITIES: dict[str, str] = {
    "UY": "Universiti Islam Antarabangsa Malaysia",
    "UE": "Universiti Teknologi Mara",
    "UK": "Universiti Kebangsaan Malaysia",
    "UM": "Universiti Malaya",
    "UJ": "Universiti Malaysia Pahang Al-Sultan Abdullah",
    "UL": "Universiti Malaysia Kelantan",
    "UH": "Universiti Malaysia Sabah",
    "UG": "Universiti Malaysia Terengganu",
    "UR": "Universiti Malaysia Perlis",
    "UW": "Universiti Malaysia Sarawak",
    "UD": "Universiti Sultan Zainal Abidin",
    "UP": "Universiti Putra Malaysia",
    "UZ": "Universiti Pertahanan Nasional Malaysia",
    "UA": "Universiti Pendidikan Sultan Idris",
    "UQ": "Universiti Sains Islam Malaysia",
    "US": "Universiti Sains Malaysia",
    "UT": "Universiti Teknologi Malaysia",
    "UC": "Universiti Teknikal Malaysia Melaka",
    "UB": "Universiti Tun Hussein Onn Malaysia",
    "UU": "Universiti Utara Malaysia",
}


@dataclass(frozen=True)
class InterestAreaDef:
    name: str
    # NEC code prefixes this area matches (PRD T1's "Programs by NEC code
    # prefix" column). A code matches if it startswith any of these and
    # doesn't startswith any of `exclude_nec_prefixes`.
    nec_prefixes: tuple[str, ...]
    # Subject groups used for the area's "excel" score (PRD T1).
    subject_groups: tuple[str, ...]
    exclude_nec_prefixes: tuple[str, ...] = field(default_factory=tuple)


# PRD T1, "Area mapping" table, verbatim.
INTEREST_AREAS: list[InterestAreaDef] = [
    InterestAreaDef(
        "Science & Technology",
        nec_prefixes=("05", "06", "07"),
        exclude_nec_prefixes=("052",),
        subject_groups=("MATHEMATICS", "SCIENCES", "TECHNICAL_ICT"),
    ),
    InterestAreaDef(
        "Business & Management",
        nec_prefixes=("041",),
        subject_groups=("MATHEMATICS", "COMMERCE"),
    ),
    InterestAreaDef(
        "Law & Governance",
        nec_prefixes=("042",),
        subject_groups=("LANGUAGES", "HUMANITIES"),
    ),
    InterestAreaDef(
        "Healthcare & Social Services",
        nec_prefixes=("09",),
        subject_groups=("SCIENCES",),
    ),
    InterestAreaDef(
        "Arts & Design",
        nec_prefixes=("021",),
        subject_groups=("ARTS",),
    ),
    InterestAreaDef(
        "Education & Humanities",
        nec_prefixes=("01", "022", "023"),
        subject_groups=("LANGUAGES", "HUMANITIES"),
    ),
    InterestAreaDef(
        "Hospitality & Tourism",
        nec_prefixes=("101",),
        subject_groups=("LANGUAGES", "COMMERCE"),
    ),
    InterestAreaDef(
        "Agriculture & Environment",
        nec_prefixes=("08", "052"),
        subject_groups=("SCIENCES",),
    ),
    InterestAreaDef(
        "Media & Communications",
        nec_prefixes=("032",),
        subject_groups=("LANGUAGES", "ARTS"),
    ),
]


def match_interest_area(nec_code: str | None) -> str | None:
    """Return the interest area name for an NEC code, or None if no prefix
    matches (PRD T1: "Programs whose NEC code matches no prefix still
    appear in Explore, but not in Best Fit").
    """
    if not nec_code:
        return None
    for area in INTEREST_AREAS:
        if any(nec_code.startswith(p) for p in area.exclude_nec_prefixes):
            continue
        if any(nec_code.startswith(p) for p in area.nec_prefixes):
            return area.name
    return None
