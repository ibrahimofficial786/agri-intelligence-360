from datetime import date, timedelta
from conftest import register
from app.services.crop_guidance import compute_calendar, stage_defs

TODAY = date(2026, 10, 1)


def test_stage_calculation(db):
    st = stage_defs(db, "Groundnut")
    for days, key in [(0, "emergence"), (9, "emergence"), (10, "vegetative"), (35, "flowering"), (60, "pod_development"), (100, "maturity")]:
        cal = compute_calendar(st, TODAY - timedelta(days=days), TODAY)
        assert cal["current_stage"]["key"] == key, days
        assert cal["days_since_sowing"] == days


def test_not_sown_and_past_duration(db):
    st = stage_defs(db, "Cotton")
    assert compute_calendar(st, TODAY + timedelta(days=5), TODAY)["phase"] == "not_sown"
    late = compute_calendar(st, TODAY - timedelta(days=400), TODAY)
    assert late["phase"] == "past_expected_duration" and late["current_stage"] is None


def test_calendar_dates_and_status(db):
    cal = compute_calendar(stage_defs(db, "Paddy"), TODAY - timedelta(days=50), TODAY)
    statuses = [c["status"] for c in cal["calendar"]]
    assert statuses[:2] == ["completed", "completed"] and statuses[2] == "current" and "upcoming" in statuses
    assert cal["calendar"][2]["start_date"] == TODAY - timedelta(days=5)
    assert cal["next_stage"]["key"] == "panicle_initiation" and cal["days_to_next_stage"] == 20


def test_every_catalog_crop_is_contiguous(db):
    for crop in ["Groundnut", "Cotton", "Paddy", "Red gram"]:
        st = stage_defs(db, crop)
        assert st and st[0]["start_day"] == 0
        assert all(a["end_day"] == b["start_day"] for a, b in zip(st, st[1:]))


def test_guidance_endpoints(client):
    h = register(client)
    r = client.post("/api/crops", json={"crop_name": "Red gram", "sowing_date": str(date.today() - timedelta(days=30)),
                                        "location": "Kurnool"}, headers=h).json()
    g = client.get(f"/api/guidance/{r['id']}", headers=h).json()
    assert g["current_stage"]["key"] == "branching" and "disclaimer" in g and g["reminders"]
    c = client.get(f"/api/crop-calendar/{r['id']}", headers=h).json()
    assert len(c["calendar"]) == 5
