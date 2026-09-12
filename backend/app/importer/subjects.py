"""Hand-written SPM subject list (plan Phase 3, task 2; proj-furtherxpert-rules skill §4).

Maps every Malay subject name (including "/" alternatives and old-syllabus
names) found in the real e-Panduan snapshot to exactly one subject `code`.
This list is hand-written and reviewed, not scraped -- the importer
(`app/importer/epanduan.py`) uses `resolve_subject_name()` to translate every
raw subject string it meets into a code, and **stops the import** with
`UnknownSubjectError` if a name isn't listed here (never guesses/skips,
PRD T2 / plan risk table).

Group codes match PRD T1's subject-groups table:
LANGUAGES, MATHEMATICS, SCIENCES, HUMANITIES, COMMERCE, TECHNICAL_ICT, ARTS.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SubjectDef:
    code: str
    name_ms: str
    name_en: str
    group: str
    old_syllabus: bool = False
    # Extra raw Malay strings (besides name_ms) seen on e-Panduan that mean
    # this exact subject -- different spelling, "/"-parts already split out,
    # ALL CAPS variants are handled by normalisation, not listed here.
    aliases: tuple[str, ...] = field(default_factory=tuple)


# --- Subject groups (PRD T1) ---
LANGUAGES = "LANGUAGES"
MATHEMATICS = "MATHEMATICS"
SCIENCES = "SCIENCES"
HUMANITIES = "HUMANITIES"
COMMERCE = "COMMERCE"
TECHNICAL_ICT = "TECHNICAL_ICT"
ARTS = "ARTS"

SUBJECT_GROUPS: dict[str, str] = {
    LANGUAGES: "Languages",
    MATHEMATICS: "Mathematics",
    SCIENCES: "Sciences",
    HUMANITIES: "Humanities",
    COMMERCE: "Commerce",
    TECHNICAL_ICT: "Technical & ICT",
    ARTS: "Arts",
}

# The base list is seeded from PRD T1's examples and the real syarat khas /
# syarat am text sampled from the live site while building this importer
# (docs/decisions/ records the parser build). New names found by a live
# import run that aren't covered here must be added, never guessed --
# `resolve_subject_name()` raises instead of skipping.
SUBJECTS: list[SubjectDef] = [
    # --- Languages ---
    SubjectDef("BM", "Bahasa Melayu", "Malay Language", LANGUAGES),
    SubjectDef("BI", "Bahasa Inggeris", "English Language", LANGUAGES),
    SubjectDef("BC", "Bahasa Cina", "Chinese Language", LANGUAGES),
    SubjectDef("BT", "Bahasa Tamil", "Tamil Language", LANGUAGES),
    SubjectDef("BA", "Bahasa Arab", "Arabic Language", LANGUAGES),
    SubjectDef("BAT", "Bahasa Arab Tinggi", "Higher Arabic Language", LANGUAGES),
    SubjectDef(
        "BAK", "Bahasa Arab Komunikasi", "Communicative Arabic", LANGUAGES, aliases=("Bahasa Arab (komunikasi)",)
    ),
    SubjectDef("BIB", "Bahasa Iban", "Iban Language", LANGUAGES),
    SubjectDef("BKD", "Bahasa Kadazandusun", "Kadazandusun Language", LANGUAGES),
    SubjectDef("BPC", "Bahasa Punjabi", "Punjabi Language", LANGUAGES),
    SubjectDef("BSM", "Bahasa Melayu Komunikatif", "Communicative Malay", LANGUAGES, old_syllabus=True),
    SubjectDef("KSM", "Kesusasteraan Melayu", "Malay Literature", LANGUAGES),
    SubjectDef("KSI", "Kesusasteraan Inggeris", "English Literature", LANGUAGES, old_syllabus=True),
    SubjectDef("BJ", "Bahasa Jepun", "Japanese Language", LANGUAGES),
    SubjectDef("BP", "Bahasa Perancis", "French Language", LANGUAGES),
    SubjectDef("BJR", "Bahasa Jerman", "German Language", LANGUAGES),
    SubjectDef("BKR", "Bahasa Korea", "Korean Language", LANGUAGES),
    SubjectDef("BSE", "Bahasa Semai", "Semai Language", LANGUAGES),
    SubjectDef("KSC", "Kesusasteraan Cina", "Chinese Literature", LANGUAGES),
    SubjectDef("KSMK", "Kesusasteraan Melayu Komunikatif", "Communicative Malay Literature", LANGUAGES, old_syllabus=True),
    SubjectDef("KST", "Kesusasteraan Tamil", "Tamil Literature", LANGUAGES),
    SubjectDef("TBA", "Turath Bahasa Arab", "Arabic Language Heritage", LANGUAGES),
    SubjectDef("AAM", "Al-lughah Al-arabiah Al-mu'asirah", "Contemporary Arabic Language", LANGUAGES),
    # --- Mathematics ---
    SubjectDef("MT", "Matematik", "Mathematics", MATHEMATICS),
    SubjectDef("MTT", "Matematik Tambahan", "Additional Mathematics", MATHEMATICS, aliases=("MATEMATIK TAMBAHAN",)),
    # --- Sciences ---
    SubjectDef("SN", "Sains", "Science", SCIENCES),
    SubjectDef("SNT", "Sains Tambahan", "Additional Science", SCIENCES, old_syllabus=True),
    SubjectDef("FZ", "Fizik", "Physics", SCIENCES),
    SubjectDef("KM", "Kimia", "Chemistry", SCIENCES),
    SubjectDef("BL", "Biologi", "Biology", SCIENCES),
    SubjectDef("STA", "Sains Tulen", "Pure Science", SCIENCES, old_syllabus=True),
    SubjectDef("SSR", "Sains Sukan", "Sports Science", SCIENCES),
    SubjectDef("SPR", "Sains Pertanian", "Agricultural Science", SCIENCES),
    SubjectDef("GAG", "Gerontologi Asas Dan Geriatrik", "Basic Gerontology and Geriatrics", SCIENCES),
    SubjectDef("SRT", "Sains Rumah Tangga", "Home Science", SCIENCES),
    SubjectDef("AHR", "Akuakultur & Haiwan Rekreasi", "Aquaculture & Recreational Animals", SCIENCES),
    SubjectDef("HHL", "Hortikultur Hiasan Dan Landskap", "Ornamental Horticulture and Landscape", SCIENCES),
    SubjectDef("PGT", "Pengeluaran Tanaman", "Crop Production", SCIENCES),
    SubjectDef("PLD", "Pengurusan Ladang", "Farm Management", SCIENCES),
    SubjectDef("PTN", "Pertanian", "Agriculture", SCIENCES),
    SubjectDef("TMN", "Tanaman Makanan", "Food Crops", SCIENCES),
    # --- Humanities ---
    SubjectDef("SJ", "Sejarah", "History", HUMANITIES),
    SubjectDef("GG", "Geografi", "Geography", HUMANITIES),
    SubjectDef("PI", "Pendidikan Islam", "Islamic Education", HUMANITIES),
    SubjectDef("PMR", "Pendidikan Moral", "Moral Education", HUMANITIES),
    SubjectDef(
        "PSK",
        "Pendidikan Syariah Islamiah",
        "Islamic Shariah Education",
        HUMANITIES,
        aliases=("Pendidikan Syari'ah Islamiah",),
    ),
    SubjectDef("TSA", "Tasawwur Islam", "Islamic Worldview", HUMANITIES),
    SubjectDef("PA", "Pengajian Al-Quran Dan Al-Sunnah", "Al-Quran and Al-Sunnah Studies", HUMANITIES),
    SubjectDef("PSY", "Pengajian Syariah", "Shariah Studies", HUMANITIES),
    SubjectDef("AWB", "Al-adab Wa Al-balaghah", "Arabic Literature and Rhetoric", HUMANITIES),
    SubjectDef("ASY", "Al-syariah", "Shariah", HUMANITIES),
    SubjectDef("HAQ", "Hifz Al Quran", "Quran Memorisation", HUMANITIES),
    SubjectDef("MAQ", "Maharat Al Quran", "Quran Skills", HUMANITIES),
    SubjectDef("MAI", "Manahij Al-'ulum Al-islamiah", "Methodology of Islamic Sciences", HUMANITIES),
    SubjectDef("PAS", "Pendidikan Al-quran Dan Al-sunnah", "Al-Quran and Al-Sunnah Education", HUMANITIES),
    SubjectDef("TAQ", "Turath Al-quran Dan Al-sunnah", "Al-Quran and Al-Sunnah Heritage", HUMANITIES),
    SubjectDef("TDI", "Turath Dirasat Islamiah", "Islamic Studies Heritage", HUMANITIES),
    SubjectDef("UAD", "Usul Al-din", "Foundations of Religion", HUMANITIES),
    SubjectDef("APAK", "Asuhan & Pendidikan Awal Kanak-kanak", "Early Childhood Care and Education", HUMANITIES),
    SubjectDef("SPS", "Sejarah Dan Pengurusan Seni", "History and Arts Management", HUMANITIES),
    # --- Commerce ---
    SubjectDef("EK", "Ekonomi", "Economics", COMMERCE),
    SubjectDef("PP", "Prinsip Perakaunan", "Principles of Accounting", COMMERCE, aliases=("PRINSIP AKAUN",)),
    SubjectDef("PN", "Perniagaan", "Business", COMMERCE, aliases=("PERDAGANGAN",)),
    SubjectDef("EKA", "Ekonomi Asas", "Basic Economics", COMMERCE),
    SubjectDef("PKU", "Pengajian Keusahawanan", "Entrepreneurship Studies", COMMERCE),
    # --- Technical & ICT ---
    SubjectDef("SK", "Sains Komputer", "Computer Science", TECHNICAL_ICT),
    SubjectDef("GKT", "Grafik Komunikasi Teknikal", "Technical Communication Graphics", TECHNICAL_ICT),
    SubjectDef("GB", "Grafik Berkomputer", "Computer Graphics", TECHNICAL_ICT, old_syllabus=True),
    SubjectDef("RC", "Reka Cipta", "Invention", TECHNICAL_ICT),
    SubjectDef("LK", "Lukisan Kejuruteraan", "Engineering Drawing", TECHNICAL_ICT, old_syllabus=True),
    SubjectDef("PKA", "Pengajian Kejuruteraan Awam", "Civil Engineering Studies", TECHNICAL_ICT),
    SubjectDef(
        "PKE",
        "Pengajian Kejuruteraan Elektrik & Elektronik",
        "Electrical & Electronic Engineering Studies",
        TECHNICAL_ICT,
        aliases=("PENGAJIAN KEJURUTERAAN ELEKTRIK DAN ELEKTRONIK",),
    ),
    SubjectDef("PKM", "Pengajian Kejuruteraan Mekanikal", "Mechanical Engineering Studies", TECHNICAL_ICT),
    SubjectDef("AK", "Asas Kelestarian", "Sustainability Basics", TECHNICAL_ICT),
    SubjectDef("KH", "Kemahiran Hidup Bersepadu", "Integrated Living Skills", TECHNICAL_ICT, old_syllabus=True),
    SubjectDef("TER", "Teknologi Elektrik Dan Elektronik", "Electrical and Electronic Technology", TECHNICAL_ICT),
    SubjectDef("TMK", "Teknologi Maklumat Dan Komunikasi", "Information and Communications Technology", TECHNICAL_ICT),
    SubjectDef("KLA", "Kejenteraan Ladang", "Farm Machinery", TECHNICAL_ICT),
    SubjectDef("KPD", "Kerja Paip Domestik", "Domestic Plumbing", TECHNICAL_ICT),
    SubjectDef("KAG", "Kimpalan Arka Dan Gas", "Arc and Gas Welding", TECHNICAL_ICT),
    SubjectDef("LDN", "Landskap Dan Nurseri", "Landscape and Nursery", TECHNICAL_ICT),
    SubjectDef("MAU", "Menservis Automobil", "Automobile Servicing", TECHNICAL_ICT),
    SubjectDef("MMO", "Menservis Motosikal", "Motorcycle Servicing", TECHNICAL_ICT),
    SubjectDef("MPED", "Menservis Peralatan Elektrik Domestik", "Domestic Electrical Appliance Servicing", TECHNICAL_ICT),
    SubjectDef(
        "MPPU",
        "Menservis Peralatan Penyejukan & Penyamanan Udara",
        "Refrigeration & Air-Conditioning Servicing",
        TECHNICAL_ICT,
    ),
    SubjectDef("PBD", "Pembinaan Domestik", "Domestic Construction", TECHNICAL_ICT),
    SubjectDef("PBP", "Pembuatan Perabot", "Furniture Making", TECHNICAL_ICT),
    SubjectDef("PMK", "Pemprosesan Makanan", "Food Processing", TECHNICAL_ICT),
    SubjectDef("PDD", "Pendawaian Domestik", "Domestic Wiring", TECHNICAL_ICT),
    SubjectDef("TKJ", "Teknologi Kejuruteraan", "Engineering Technology", TECHNICAL_ICT),
    SubjectDef("KDP", "Katering Dan Penyajian", "Catering and Food Service", TECHNICAL_ICT),
    # --- Arts ---
    SubjectDef("PSV", "Pendidikan Seni Visual", "Visual Arts Education", ARTS),
    SubjectDef("RBG", "Reka Bentuk Grafik", "Graphic Design", ARTS),
    SubjectDef("PM", "Produksi Multimedia", "Multimedia Production", ARTS),
    SubjectDef("BU", "Bina Urus", "Home Management", ARTS, old_syllabus=True),
    SubjectDef("RBGD", "Reka Bentuk Grafik Digital", "Digital Graphic Design", ARTS),
    SubjectDef("RBI", "Reka Bentuk Industri", "Industrial Design", ARTS),
    SubjectDef("RBK", "Reka Bentuk Kraf", "Craft Design", ARTS),
    SubjectDef("MMK", "Multimedia Kreatif", "Creative Multimedia", ARTS),
    SubjectDef("PRT", "Produksi Reka Tanda", "Signage Design Production", ARTS),
    SubjectDef("HD", "Hiasan Dalaman", "Interior Decoration", ARTS),
    SubjectDef("HDA", "Hiasan Dalaman Asas", "Basic Interior Decoration", ARTS),
    SubjectDef("AMU", "Alat Muzik Utama", "Principal Musical Instrument", ARTS),
    SubjectDef("APT", "Apresiasi Tari", "Dance Appreciation", ARTS),
    SubjectDef("ATM", "Aural Dan Teori Muzik", "Aural and Music Theory", ARTS),
    SubjectDef("KOT", "Koreografi Tari", "Dance Choreography", ARTS),
    SubjectDef("LAK", "Lakonan", "Acting", ARTS),
    SubjectDef("LUK", "Lukisan", "Drawing", ARTS),
    SubjectDef("MZK", "Muzik Komputer", "Computer Music", ARTS),
    SubjectDef("PMZ", "Pendidikan Muzik", "Music Education", ARTS),
    SubjectDef("PSP", "Penulisan Skrip", "Script Writing", ARTS),
    SubjectDef("PSPR", "Produksi Seni Persembahan", "Performing Arts Production", ARTS),
    SubjectDef("SH2", "Seni Halus 2d", "Fine Art 2D", ARTS),
    SubjectDef("SH3", "Seni Halus 3d", "Fine Art 3D", ARTS),
    SubjectDef("SIN", "Sinografi", "Scenography", ARTS),
    SubjectDef("TAR", "Tarian", "Dance", ARTS),
    SubjectDef("RJP", "Rekaan Dan Jahitan Pakaian", "Fashion Design and Sewing", ARTS),
]

# code -> definition
SUBJECTS_BY_CODE: dict[str, SubjectDef] = {s.code: s for s in SUBJECTS}


def _normalize(name: str) -> str:
    """Upper-case, collapse whitespace, drop a trailing period -- so
    "Bahasa Melayu", "BAHASA MELAYU", and "Bahasa Melayu." all match one key.
    """
    cleaned = " ".join(name.strip().split())
    cleaned = cleaned.rstrip(".")
    return cleaned.upper()


def _build_alias_table() -> dict[str, str]:
    table: dict[str, str] = {}
    for subject in SUBJECTS:
        table[_normalize(subject.name_ms)] = subject.code
        for alias in subject.aliases:
            table[_normalize(alias)] = subject.code
    return table


NAME_TO_CODE: dict[str, str] = _build_alias_table()


class UnknownSubjectError(Exception):
    """Raised when a raw e-Panduan subject name has no entry in SUBJECTS.

    Per plan Phase 3 task 2 / risk table: an unmapped name **stops the
    import**. The importer never guesses or silently skips a subject.
    """

    def __init__(self, raw_name: str):
        self.raw_name = raw_name
        super().__init__(
            f"Unknown SPM subject name from e-Panduan: {raw_name!r} -- add it to "
            "app/importer/subjects.py (SUBJECTS) before re-running the import."
        )


def resolve_subject_name(raw_name: str) -> str:
    """Return the subject `code` for a raw Malay name from e-Panduan.

    Raises UnknownSubjectError if the name isn't mapped -- see module
    docstring and plan Phase 3 task 2.
    """
    code = NAME_TO_CODE.get(_normalize(raw_name))
    if code is None:
        raise UnknownSubjectError(raw_name)
    return code
