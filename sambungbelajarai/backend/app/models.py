from typing import Dict, List, Optional

from pydantic import BaseModel


class Program(BaseModel):
    id: str
    name: str
    institution_id: str
    min_requirements: Dict[str, str]
    field: str
    duration_years: int
    mode: str
    tuition_fee_rm: int


class Institution(BaseModel):
    id: str
    name: str
    geo: Dict[str, float]
    region: str
    type: str


class StudentInput(BaseModel):
    grades: Optional[Dict[str, str]] = None
    interests: List[str]
    # User's current location or preferred base location (optional)
    location: Optional[str] = None
    # One or more preferred Malaysian states for studying (optional)
    preferred_locations: Optional[List[str]] = None
    # User's home state set in profile (optional pass-through)
    home_state: Optional[str] = None


class Profile(BaseModel):
    home_state: Optional[str] = None
    academic_results: Dict[str, str] = {}
    interest_scores: Dict[str, int] = {}
    interests: List[str] = []
    qna_answers: List[Optional[int]] = []
