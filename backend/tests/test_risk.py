from datetime import date, timedelta
from conftest import register
from app.models.models import RiskReport
from app.services.community_risk import generate_alerts


def add(db, uid, area="A", ago=1, problem="Leaf spot", crop="Groundnut", district="Kurnool"):
    db.add(RiskReport(user_id=uid, crop_name=crop, district=district, area=area, problem=problem,
                      report_date=date.today() - timedelta(days=ago)))
    db.commit()


def test_no_alert_below_threshold_or_single_reporter(db):
    add(db, 1); add(db, 2)
    assert generate_alerts(db) == []
    add(db, 1)  # 3 reports but only 2 reporters -> alert; make a single-reporter case in another group
    for _ in range(4):
        add(db, 5, problem="Rust")
    assert [a["problem"] for a in generate_alerts(db)] == ["Leaf spot"]


def test_alert_content_and_grouping(db):
    for uid, area in [(1, "Dhone"), (2, "Orvakal"), (3, "Kurnool")]:
        add(db, uid, area)
    add(db, 4, problem="  leaf SPOT ")  # normalised into same group
    add(db, 4, crop="Cotton")           # different crop, separate group
    add(db, 4, district="Anantapur")    # different district, separate group
    a = generate_alerts(db)
    assert len(a) == 1 and a[0]["report_count"] == 4 and a[0]["reporter_count"] == 4
    assert a[0]["status"] == "possible_risk" and "not confirmed" in a[0]["explanation"]
    assert set(a[0]["areas"]) >= {"Dhone", "Orvakal"}


def test_old_reports_excluded(db):
    for uid in (1, 2, 3):
        add(db, uid, ago=40)
    assert generate_alerts(db) == []


def test_submit_endpoint_and_alert_notification(client, db):
    hs = [register(client, f"u{i}@example.com") for i in range(3)]
    client.post("/api/crops", json={"crop_name": "Groundnut", "sowing_date": str(date.today() - timedelta(days=30)),
                                    "location": "Kurnool"}, headers=hs[0])
    form = {"crop_name": "Groundnut", "district": "Kurnool", "area": "Dhone", "report_date": str(date.today()), "problem": "Leaf spot"}
    outs = [client.post("/api/risk/reports", data=form, headers=h).json() for h in hs]
    assert [o["alert_triggered"] for o in outs] == [False, False, True]
    assert "not a confirmed diagnosis" in outs[0]["note"]
    alerts = client.get("/api/risk/alerts", headers=hs[0]).json()["alerts"]
    assert alerts and alerts[0]["report_count"] == 3
    assert any(n["kind"] == "community_risk" for n in client.get("/api/notifications", headers=hs[0]).json())
    bad = dict(form, report_date=str(date.today() + timedelta(days=3)))
    assert client.post("/api/risk/reports", data=bad, headers=hs[0]).status_code == 422
    assert client.post("/api/risk/reports", data=dict(form, crop_name="Banana"), headers=hs[0]).status_code == 422
    assert client.get("/api/risk/alerts").status_code == 401


def test_error_response_hides_internals(client):
    r = client.get("/api/crops/abc", headers=register(client))
    assert r.status_code == 422 and "Traceback" not in r.text
