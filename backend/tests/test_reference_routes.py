"""API tests for the reference-data routes (PRD T6, plan Phase 3 task 6):
`GET /subjects`, `GET /universities`, `GET /programs`, `GET /programs/{code}`.

These run against the real test database, seeded by the Phase 3 data
migration (`migrations/versions/6676e66b52e5_...py`) that `tests/conftest.py`
runs once per test session -- no fixtures are inserted here, the routes are
exercised against the actual loaded 2026/2027 snapshot.
"""


def test_read_subjects_includes_known_subjects(client) -> None:
    resp = client.get("/subjects")
    assert resp.status_code == 200
    subjects = {s["code"]: s for s in resp.json()}
    assert "BM" in subjects
    assert subjects["BM"]["name_ms"] == "Bahasa Melayu"
    assert subjects["BM"]["group"] == "LANGUAGES"
    assert "SJ" in subjects


def test_read_universities_includes_known_universities(client) -> None:
    resp = client.get("/universities")
    assert resp.status_code == 200
    unis = {u["code"]: u["name"] for u in resp.json()}
    assert unis.get("UE") == "Universiti Teknologi Mara"
    assert unis.get("UP") == "Universiti Putra Malaysia"


def test_read_programs_returns_ua_diplomas(client) -> None:
    resp = client.get("/programs")
    assert resp.status_code == 200
    programs = resp.json()
    assert len(programs) > 0
    for program in programs:
        assert program["code"][0] == "U"
        assert program["code"][2] == "4"


def test_read_programs_filters_by_university(client) -> None:
    resp = client.get("/programs", params={"university": "UE"})
    assert resp.status_code == 200
    programs = resp.json()
    assert programs
    assert all(p["university_code"] == "UE" for p in programs)


def test_read_programs_text_search(client) -> None:
    resp = client.get("/programs", params={"q": "Sains Komputer"})
    assert resp.status_code == 200
    programs = resp.json()
    assert programs
    assert all("sains komputer" in p["name"].lower() for p in programs)


def test_read_program_detail_ue4481001(client) -> None:
    resp = client.get("/programs/UE4481001")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "UE4481001"
    assert body["university_code"] == "UE"
    assert body["bumiputera_only"] is True
    assert "Source: e-Panduan UPU, KPT, sesi" in body["source_credit"]
    categories = {r["category"] for r in body["requirements"]}
    assert "A" in categories
    general_categories = {r["category"] for r in body["general_requirements"]}
    assert "A" in general_categories
    a_requirement = next(r for r in body["requirements"] if r["category"] == "A")
    assert a_requirement["text_ms"]
    assert isinstance(a_requirement["rules"], dict)


def test_read_program_detail_not_found(client) -> None:
    resp = client.get("/programs/DOES-NOT-EXIST")
    assert resp.status_code == 404
