from app.main import check_eligibility
from app.models import StudentInput


def test_eligibility_basic():
    data = StudentInput(
        grades={"Math": "A", "English": "B"},
        interests=["IT"],
        location="Johor",
    )
    res = check_eligibility(data)
    assert any(p["eligibility"] == "Eligible" for p in res["eligible_programs"])
