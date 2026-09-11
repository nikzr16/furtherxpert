import json
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .models import Profile, StudentInput
from .utils import meets_min_requirements, normalize_subject_names


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


@app.get("/institutions")
def list_institutions() -> List[Dict[str, Any]]:
    return _load_json("institutions.json")


@app.get("/programs")
def list_programs() -> List[Dict[str, Any]]:
    return _load_json("programs.json")
