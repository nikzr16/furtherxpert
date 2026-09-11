from typing import Dict, Iterable, List, Tuple

from geopy.distance import geodesic


GRADE_ORDER: Dict[str, int] = {
    "A+": 1,
    "A": 2,
    "A-": 3,
    "B+": 4,
    "B": 5,
    "B-": 6,
    "C+": 7,
    "C": 8,
    "C-": 9,
    "D": 10,
    "E": 11,
    "F": 12,
}


def meets_min_requirements(student_grades: Dict[str, str], min_requirements: Dict[str, str]) -> bool:
    for subject, min_grade in min_requirements.items():
        student_grade = student_grades.get(subject)
        if student_grade is None:
            return False
        if GRADE_ORDER.get(student_grade, 999) > GRADE_ORDER.get(min_grade, 999):
            return False
    return True


# Canonicalize subject names (e.g., BI -> English, Matematik -> Math)
_SUBJECT_ALIASES: Dict[str, str] = {
    # English
    "english": "English",
    "english language": "English",
    "bahasa inggeris": "English",
    "bi": "English",
    # Math
    "math": "Math",
    "mathematics": "Math",
    "matematik": "Math",
    # Additional Mathematics (kept distinct from Math)
    "additional mathematics": "Additional Mathematics",
    "add maths": "Additional Mathematics",
    "add math": "Additional Mathematics",
    "matematik tambahan": "Additional Mathematics",
    # Bahasa Melayu
    "bm": "Bahasa Melayu",
    "bahasa melayu": "Bahasa Melayu",
    "malay": "Bahasa Melayu",
}


def normalize_subject_names(grades: Dict[str, str]) -> Dict[str, str]:
    normalized: Dict[str, str] = {}
    for raw_subject, grade in (grades or {}).items():
        key = (raw_subject or "").strip().lower()
        canonical = _SUBJECT_ALIASES.get(key, raw_subject)
        # If duplicate canonical subject appears, keep the better grade
        if canonical in normalized:
            prev = normalized[canonical]
            if GRADE_ORDER.get(grade, 999) < GRADE_ORDER.get(prev, 999):
                normalized[canonical] = grade
        else:
            normalized[canonical] = grade
    return normalized


def nearest_institutions(
    user_coords: Tuple[float, float],
    institutions: Iterable[Dict[str, object]],
    max_results: int = 5,
) -> List[Dict[str, object]]:
    with_dist = []
    for inst in institutions:
        lat = float(inst.get("geo", {}).get("lat", 0.0))
        lon = float(inst.get("geo", {}).get("lon", 0.0))
        if lat == 0.0 and lon == 0.0:
            continue
        d_km = geodesic(user_coords, (lat, lon)).km
        with_dist.append({**inst, "distance_km": d_km})
    with_dist.sort(key=lambda x: x["distance_km"])
    return with_dist[:max_results]
