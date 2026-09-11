import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .llm import SYSTEM_PROMPT, call_llm_text, validate_recommendations_json
from .models import Profile, RecommendationResponse, StudentInput
from .utils import meets_min_requirements, GRADE_ORDER, normalize_subject_names


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
load_dotenv(BASE_DIR / ".env")

# Map fine-grained interests/tags to broader categories
INTEREST_CATEGORY_MAP: Dict[str, List[str]] = {
    "Science & Technology": [
        "IT", "Computer Science", "Data", "Science", "Engineering", "Environment", "Sains Komputer"
    ],
    "Business & Management": [
        "Business", "Finance", "Communications", "Logistics", "Perdagangan", "Ekonomi", "Prinsip Perakaunan"
    ],
    "Healthcare & Social Services": [
        "Healthcare", "Social Work"
    ],
    "Arts & Design": [
        "Arts", "Design", "Architecture", "Seni Visual"
    ],
    "Education & Humanities": [
        "Education", "Language", "Kesusasteraan Melayu", "English Literature"
    ],
    "Law & Governance": [
        "Law"
    ],
    "Hospitality & Tourism": [
        "Hospitality"
    ],
    "Agriculture & Environment": [
        "Agriculture", "Environment"
    ],
    "Media & Communications": [
        "Communications"
    ],
}


def infer_interest_categories(interests: List[str]) -> List[str]:
    categories: List[str] = []
    seen = set()
    norm = set((i or "").strip().lower() for i in interests)
    # Direct category matches
    for category in INTEREST_CATEGORY_MAP.keys():
        if category.lower() in norm and category not in seen:
            seen.add(category)
            categories.append(category)
    # Tag-to-category mapping
    for category, tags in INTEREST_CATEGORY_MAP.items():
        for tag in tags:
            if tag.lower() in norm and category not in seen:
                seen.add(category)
                categories.append(category)
                break
    return categories or ["General"]


def categories_from_scores(scores: Dict[str, int]) -> List[str]:
    cat_scores: Dict[str, int] = {}
    for category, tags in INTEREST_CATEGORY_MAP.items():
        s = sum(scores.get(tag, 0) for tag in tags)
        if s > 0:
            cat_scores[category] = s
    if not cat_scores:
        return []
    ordered = sorted(cat_scores.items(), key=lambda kv: kv[1], reverse=True)
    return [c for c, _ in ordered[:5]]


# System prompt for free-form AskAI chat (STRICT data-only)
CHAT_SYSTEM_PROMPT = (
    "You are an academic guidance assistant for Malaysian SPM graduates. "
    "STRICT RULES: Use ONLY the entities provided in AllowedInstitutions, AllowedPrograms, AllowedLoans, and AllowedScholarships. "
    "Do NOT invent or reference institutions/programs/loans/scholarships outside these lists. "
    "If the user's request requires items not present, say: 'Not available in our dataset' and suggest narrowing the question. "
    "Tailor answers using the provided profile context (grades, interests, location, QnA). "
    "Be concise, factual, and actionable. Ask at most one brief clarifying question if needed."
)


# Approximate centroids for Malaysian states/FT (lat, lon)
STATE_CENTROIDS: Dict[str, Dict[str, float]] = {
    "johor": {"lat": 1.85, "lon": 103.0},
    "kedah": {"lat": 6.12, "lon": 100.37},
    "kelantan": {"lat": 5.29, "lon": 102.27},
    "melaka": {"lat": 2.20, "lon": 102.25},
    "negeri sembilan": {"lat": 2.73, "lon": 102.25},
    "pahang": {"lat": 3.81, "lon": 103.33},
    "penang": {"lat": 5.35, "lon": 100.28},
    "pulau pinang": {"lat": 5.35, "lon": 100.28},
    "perak": {"lat": 4.60, "lon": 101.07},
    "perlis": {"lat": 6.44, "lon": 100.20},
    "sabah": {"lat": 5.42, "lon": 116.73},
    "sarawak": {"lat": 1.55, "lon": 110.36},
    "selangor": {"lat": 3.07, "lon": 101.52},
    "terengganu": {"lat": 5.33, "lon": 103.14},
    "kuala lumpur": {"lat": 3.14, "lon": 101.69},
    "putrajaya": {"lat": 2.93, "lon": 101.69},
    "labuan": {"lat": 5.28, "lon": 115.24},
}


def _norm_state(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    s = s.strip().lower()
    if s in ("kl", "wilayah persekutuan kuala lumpur"):
        return "kuala lumpur"
    if s == "penang":
        return "pulau pinang"
    return s


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    from math import radians, sin, cos, sqrt, atan2
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return round(R * c, 1)


def _load_json(name: str) -> Any:
    with open(DATA_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


PROFILE_PATH = DATA_DIR / "profile.json"


def _load_profile() -> Dict[str, Any]:
    if PROFILE_PATH.exists():
        with open(PROFILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    # default profile
    return {"home_state": None, "academic_results": {}, "interest_scores": {}, "interests": [], "qna_answers": []}


def _save_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)
    return profile


app = FastAPI(title="SambungBelajarmu.ai API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/eligibility")
def check_eligibility(data: StudentInput) -> Dict[str, List[Dict[str, Any]]]:
    programs = _load_json("programs.json")
    profile = _load_profile()
    grades = normalize_subject_names(data.grades or profile.get("academic_results") or {})
    interests = data.interests or profile.get("interests") or []
    # Compute category preference weights from profile interest_scores if present
    score_map: Dict[str, int] = {}
    scores = profile.get("interest_scores") or {}
    for category, tags in INTEREST_CATEGORY_MAP.items():
        score_map[category] = sum(scores.get(tag, 0) for tag in tags)
    # Field to category mapping for programs
    FIELD_TO_CATEGORY = {
        "it": "Science & Technology",
        "computer science": "Science & Technology",
        "business": "Business & Management",
    }
    interest_categories = infer_interest_categories(interests)
    eligible: List[Dict[str, Any]] = []
    for p in programs:
        if meets_min_requirements(grades, p.get("min_requirements", {})):
            field = (p.get("field") or "").strip().lower()
            category = FIELD_TO_CATEGORY.get(field)
            base = 1 if (category in interest_categories) else 0
            weighted = base + (score_map.get(category or "", 0))
            eligible.append({**p, "eligibility": "Eligible", "score": weighted})
    # If any have scores >0, keep only those; else keep all
    if any((e.get("score", 0) or 0) > 0 for e in eligible):
        eligible = [e for e in eligible if (e.get("score", 0) or 0) > 0]
    eligible.sort(key=lambda e: e.get("score", 0), reverse=True)
    return {"eligible_programs": eligible}


@app.get("/profile")
def get_profile() -> Dict[str, Any]:
    return _load_profile()


@app.post("/profile")
def set_profile(profile: Profile) -> Dict[str, Any]:
    # Persist profile JSON to disk
    computed_categories = categories_from_scores(profile.interest_scores or {})
    final_interests = profile.interests or computed_categories
    payload = {
        "home_state": profile.home_state,
        "academic_results": profile.academic_results,
        "interest_scores": profile.interest_scores,
        "interests": final_interests,
        "qna_answers": profile.qna_answers,
    }
    return _save_profile(payload)


@app.get("/loans")
def list_loans() -> List[Dict[str, Any]]:
    return _load_json("loans.json")


@app.get("/institutions")
def list_institutions() -> List[Dict[str, Any]]:
    return _load_json("institutions.json")


@app.get("/programs")
def list_programs() -> List[Dict[str, Any]]:
    return _load_json("programs.json")


@app.get("/financial_aid")
def financial_aid() -> List[Dict[str, Any]]:
    loans = _load_json("loans.json")
    scholarships = _load_json("scholarships.json")
    combined: List[Dict[str, Any]] = []
    for l in loans:
        combined.append({
            **l,
            "type": "Loan",
            "provider": "PTPTN" if "ptptn" in l.get("name", "").lower() else None,
        })
    for s in scholarships:
        combined.append({
            **s,
            "type": "Scholarship",
            "provider": "MARA" if "mara" in s.get("name", "").lower() else None,
        })
    return combined


from pydantic import BaseModel


class InstitutionFilter(BaseModel):
    preferred_locations: Optional[List[str]] = None
    home_state: Optional[str] = None


@app.post("/institutions_filtered")
def institutions_filtered(flt: InstitutionFilter) -> List[Dict[str, Any]]:
    institutions = _load_json("institutions.json")
    loans = _load_json("loans.json")
    scholarships = _load_json("scholarships.json")
    programs = _load_json("programs.json")
    profile = _load_profile()
    preferred = flt.preferred_locations or []
    home_state = flt.home_state or profile.get("home_state")

    # Map institutions that offer online programs (ODL)
    online_institution_ids = {p["institution_id"] for p in programs if p.get("mode", "").lower() == "online"}

    def region_norm(r: str) -> str:
        r = (r or "").strip().lower()
        return "kuala lumpur" if r in ("kl", "kuala lumpur") else r

    selected_regions = {region_norm(x) for x in preferred if x and x.upper() != "ODL"}
    include_odl = any((x or "").strip().upper() == "ODL" for x in preferred)

    # Filter institutions by preferred regions/ODL; if none selected, include all
    filtered = []
    for inst in institutions:
        inst_region = region_norm(inst.get("region", ""))
        ok_region = not selected_regions or inst_region in selected_regions
        ok_odl = include_odl and inst.get("id") in online_institution_ids
        if selected_regions or include_odl:
            if ok_region or ok_odl:
                filtered.append(inst)
        else:
            filtered.append(inst)

    # Compute distances from home_state if available
    home_norm = _norm_state(home_state)
    home_geo = STATE_CENTROIDS.get(home_norm) if home_norm else None
    for inst in filtered:
        geo = inst.get("geo") or {}
        if home_geo and geo:
            inst["distance_km"] = _haversine_km(home_geo["lat"], home_geo["lon"], geo.get("lat", 0.0), geo.get("lon", 0.0))
        else:
            inst["distance_km"] = None

    # Sort by distance when possible
    if home_geo:
        filtered.sort(key=lambda i: (i.get("distance_km") is None, i.get("distance_km", 0)))

    # Ensure at least 10 institutions: top-up with nearest others
    if len(filtered) < 10:
        remaining = [i for i in institutions if i not in filtered]
        # compute distance for remaining
        for inst in remaining:
            geo = inst.get("geo") or {}
            if home_geo and geo:
                inst["distance_km"] = _haversine_km(home_geo["lat"], home_geo["lon"], geo.get("lat", 0.0), geo.get("lon", 0.0))
            else:
                inst["distance_km"] = None
        remaining.sort(key=lambda i: (i.get("distance_km") is None, i.get("distance_km", 0)))
        to_add = 10 - len(filtered)
        filtered.extend(remaining[:to_add])

    return filtered[:10]


@app.post("/recommend", response_model=RecommendationResponse)
def recommend(data: StudentInput) -> RecommendationResponse:
    programs = _load_json("programs.json")
    institutions = _load_json("institutions.json")
    loans = _load_json("loans.json")
    scholarships = _load_json("scholarships.json")

    profile = _load_profile()
    academic_results_json = json.dumps(normalize_subject_names(profile.get("academic_results") or {}), ensure_ascii=False)

    # Choose a location preference for display/fallbacks
    chosen_location = None
    if data.preferred_locations and len(data.preferred_locations) > 0:
        chosen_location = ", ".join(data.preferred_locations)
    elif data.home_state:
        chosen_location = data.home_state
    elif data.location:
        chosen_location = data.location
    else:
        chosen_location = profile.get("home_state") or "Malaysia"

    interests = data.interests or profile.get("interests") or []
    interest_categories = infer_interest_categories(interests)

    prompt = (
        "Student profile:"
        f"\nGrades: {data.grades}"
        f"\nInterest Categories: {interest_categories}"
        f"\nPreferred Locations: {data.preferred_locations or []}"
        f"\nHome State: {profile.get('home_state')}"
        "\nUse only these programs/institutions/loans by name from provided JSON. "
        "Return JSON per schema."
    )

    try:
        system = SYSTEM_PROMPT.replace("{{ACADEMIC_RESULTS}}", academic_results_json)
        raw = call_llm_text(system, prompt)
        parsed = validate_recommendations_json(raw)
    except Exception:
        grades_fallback = normalize_subject_names(data.grades or (profile.get("academic_results") or {}))
        eligible = [
            p for p in programs if meets_min_requirements(grades_fallback, p.get("min_requirements", {}))
        ]
        limited = eligible[:3]
        parsed = {
            "recommendations": [
                {
                    "program_name": p["name"],
                    "institution": next(i["name"] for i in institutions if i["id"] == p["institution_id"]),
                    "reason": "Meets minimum SPM requirements",
                    "eligibility": "Eligible",
                    "location": chosen_location,
                    "financing": [
                        {"name": loans[0]["name"], "eligible": True}
                    ],
                }
                for p in limited
            ],
            "loans": [l["name"] for l in loans[:2]],
            "institutions": [
                next(i["name"] for i in institutions if i["id"] == p["institution_id"]) for p in limited
            ],
            "disclaimer": "This is informational only. Verify details with official sources.",
            "sources": ["programs.json", "loans.json", "institutions.json"],
        }

    return RecommendationResponse(**parsed)


# Simple chat endpoint for AskAI page
from pydantic import BaseModel


class ChatRequest(BaseModel):
    query: str


class ChatResponse(BaseModel):
    text: str


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    # Try AI-powered response first, enriched with profile context
    programs = _load_json("programs.json")
    institutions = _load_json("institutions.json")
    loans = _load_json("loans.json")
    scholarships = _load_json("scholarships.json")

    profile = _load_profile()
    academic_results = normalize_subject_names(profile.get("academic_results") or {})
    interest_scores = profile.get("interest_scores") or {}
    interests = profile.get("interests") or categories_from_scores(interest_scores)
    qna_answers = profile.get("qna_answers") or []
    home_state = profile.get("home_state") or None

    allowed_entities = {
        "AllowedInstitutions": [i.get("name") for i in institutions],
        "AllowedPrograms": [p.get("name") for p in programs],
        "AllowedLoans": [l.get("name") for l in loans],
        "AllowedScholarships": [s.get("name") for s in scholarships],
    }

    context = {
        "academic_results": academic_results,
        "home_state": home_state,
        "interests": interests,
        "interest_scores": interest_scores,
        "qna_answers": qna_answers,
    }
    chat_prompt = (
        f"User question:\n{(req.query or '').strip()}\n\n"
        f"Profile context (JSON):\n{json.dumps(context, ensure_ascii=False)}\n\n"
        f"Use ONLY these entities. If not listed, say it's not in our dataset.\n"
        f"{json.dumps(allowed_entities, ensure_ascii=False)}"
    )
    try:
        ai_text = call_llm_text(CHAT_SYSTEM_PROMPT, chat_prompt)
        return ChatResponse(text=ai_text)
    except Exception:
        # Fallback to deterministic dataset-only logic
        pass

    # Interest signals from QnA/profile
    ordered_tags = sorted(interest_scores.items(), key=lambda kv: kv[1], reverse=True)
    top_interest_tags = [k for k, v in ordered_tags if v > 0][:5]
    has_interest = any((v or 0) > 0 for v in interest_scores.values())
    # When no interests provided, do not infer or apply interest categories
    categories = categories_from_scores(interest_scores) if has_interest else []

    home_state = profile.get("home_state") or None

    inst_by_id = {i["id"]: i for i in institutions}

    FIELD_TO_CATEGORY = {
        "it": "Science & Technology",
        "computer science": "Science & Technology",
        "business": "Business & Management",
    }

    score_map: Dict[str, int] = {}
    for category, tags in INTEREST_CATEGORY_MAP.items():
        score_map[category] = sum(interest_scores.get(tag, 0) for tag in tags)

    def _norm(s: str) -> str:
        return (s or "").strip().lower()

    home_norm = _norm(home_state) if home_state else None

    # Parse simple intents from user query (deterministic)
    q = (req.query or "").strip().lower()
    requested_fields: set = set()
    if any(k in q for k in ["business", "account", "finance", "marketing", "econ"]):
        requested_fields.add("business")
    if any(k in q for k in ["it", "computer", "software", "network", "cs"]):
        requested_fields.add("it")
    if any(k in q for k in ["design", "multimedia", "ui/ux", "graphic"]):
        requested_fields.add("design")
    if any(k in q for k in ["hospitality", "culinary", "f&b", "hotel"]):
        requested_fields.add("hospitality")

    require_same_state = any(
        phrase in q for phrase in ["same state", "my state", "same state of mine", "in the same state"]
    )

    # Build matches from data only
    matched: List[Dict[str, Any]] = []
    for p in programs:
        if not meets_min_requirements(academic_results, p.get("min_requirements", {})):
            continue
        field = _norm(p.get("field", ""))
        # If user requested specific field(s), enforce it
        if requested_fields and field not in requested_fields:
            continue
        category = FIELD_TO_CATEGORY.get(field)
        base_interest = 1 if (has_interest and category and (category in categories)) else 0
        weighted_interest = base_interest + (score_map.get(category or "", 0) if has_interest else 0)
        inst = inst_by_id.get(p.get("institution_id")) or {}
        inst_region = _norm(inst.get("region", ""))
        # If user asked for same state, enforce region match to home_state
        if require_same_state and home_norm and inst_region != home_norm:
            continue
        loc_bonus = 2 if (home_norm and inst_region and inst_region == home_norm) else 0
        odl_bonus = 1 if (p.get("mode", "").strip().lower() == "online") else 0
        total_score = weighted_interest + loc_bonus + odl_bonus
        if total_score > 0:
            matched.append({**p, "_institution": inst, "_score": total_score})

    matched.sort(key=lambda x: x.get("_score", 0), reverse=True)
    top_matched = matched[:5]

    def summarize_eligibility(p: Dict[str, Any]) -> str:
        reqs = p.get("min_requirements", {}) or {}
        parts: List[str] = []
        for subj, min_g in reqs.items():
            got = academic_results.get(subj)
            if got is not None:
                parts.append(f"{subj} {got} (min {min_g})")
        return ", ".join(parts) if parts else "Meets stated minimum requirements"

    def eligibility_gaps(p: Dict[str, Any]) -> List[str]:
        reqs = p.get("min_requirements", {}) or {}
        gaps: List[str] = []
        for subj, min_g in reqs.items():
            got = academic_results.get(subj)
            if got is None:
                gaps.append(f"{subj}: missing (min {min_g})")
            else:
                if GRADE_ORDER.get(got, 999) > GRADE_ORDER.get(min_g, 999):
                    gaps.append(f"{subj}: {got} < min {min_g}")
        return gaps

    def interest_reason(p: Dict[str, Any]) -> str:
        field = _norm(p.get("field", ""))
        category = FIELD_TO_CATEGORY.get(field)
        bits: List[str] = []
        if not has_interest:
            return ""
        if category:
            bits.append(f"aligns with your interest category: {category}")
        if top_interest_tags:
            bits.append(f"top tags: {', '.join(top_interest_tags)}")
        return "; ".join(bits) if bits else "fits your broad interests"

    def location_reason(p: Dict[str, Any]) -> str:
        inst = p.get("_institution") or {}
        region = inst.get("region")
        mode = (p.get("mode") or "").strip()
        if home_state and region and _norm(region) == home_norm:
            return f"near your home state ({region})"
        if mode.lower() == "online":
            return "available fully online (ODL)"
        return f"offered in {region}" if region else "location not specified"

    lines: List[str] = []
    lines.append("Based on your profile and question, here are options strictly from our dataset:")
    if not top_matched:
        # Provide transparent reason from data
        # Gather candidate programs filtered by prompt (field/state) to explain gaps
        explanation_candidates: List[Dict[str, Any]] = []
        for p in programs:
            fld = _norm(p.get("field", ""))
            if requested_fields and fld not in requested_fields:
                continue
            inst = inst_by_id.get(p.get("institution_id")) or {}
            inst_region = _norm(inst.get("region", ""))
            if require_same_state and home_norm and inst_region != home_norm:
                continue
            explanation_candidates.append({**p, "_institution": inst})

        if not explanation_candidates:
            lines.append("- No programs found that match the requested field/state in our dataset.")
        else:
            lines.append("- No immediate matches due to minimum entry requirements. Details:")
            for p in explanation_candidates[:2]:
                inst = p.get("_institution") or {}
                gaps = eligibility_gaps(p)
                gap_txt = "; ".join(gaps) if gaps else "Other constraints"
                lines.append(f"  • {p.get('name')} — {inst.get('name','Unknown')}: {gap_txt}")
            lines.append("Tip: Add required SPM subjects/grades in Profile to unlock eligible options.")
    else:
        for i, m in enumerate(top_matched[:3], start=1):
            inst = m.get("_institution") or {}
            fee = m.get("tuition_fee_rm")
            fee_txt = f"RM {fee:,}" if isinstance(fee, int) else "N/A"
            why_parts = [f"Eligibility: {summarize_eligibility(m)}", f"Location/Mode: {location_reason(m)}"]
            i_reason = interest_reason(m)
            if i_reason:
                why_parts.insert(1, f"Interests: {i_reason}")
            lines.append(
                f"{i}. {m.get('name')} — {inst.get('name','Unknown')} ({m.get('mode','')})\n   Field: {m.get('field','')} • Tuition: {fee_txt}\n   Why: "
                + " | ".join(why_parts)
            )

    # Append compact list of up to 5 matching courses (Explore-aligned)
    if top_matched:
        lines.append("\nAvailable courses that suit you:")
        for m in top_matched:
            inst = m.get("_institution") or {}
            lines.append(f"- {m.get('name')} — {inst.get('name','Unknown')} ({m.get('mode','')})")

    return ChatResponse(text="\n".join(lines))
