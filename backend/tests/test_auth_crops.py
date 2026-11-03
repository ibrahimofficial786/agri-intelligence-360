from datetime import date, timedelta
from conftest import register


def test_register_login_me_and_no_hash_leak(client):
    h = register(client)
    r = client.post("/api/auth/login", json={"email": "a@example.com", "password": "Passw0rd!"})
    assert r.status_code == 200 and "password" not in r.text
    me = client.get("/api/auth/me", headers=h).json()
    assert me["email"] == "a@example.com" and "password_hash" not in me


def test_register_validation_and_duplicates(client):
    register(client)
    assert client.post("/api/auth/register", json={"email": "a@example.com", "password": "Passw0rd!", "full_name": "X Y"}).status_code == 409
    assert client.post("/api/auth/register", json={"email": "bad", "password": "Passw0rd!", "full_name": "X Y"}).status_code == 422
    assert client.post("/api/auth/register", json={"email": "b@example.com", "password": "short", "full_name": "X Y"}).status_code == 422


def test_login_wrong_password(client):
    register(client)
    assert client.post("/api/auth/login", json={"email": "a@example.com", "password": "nope12345"}).status_code == 401


def test_protected_endpoints_need_token(client):
    for path in ["/api/crops", "/api/dashboard/summary", "/api/notifications", "/api/health/reports"]:
        assert client.get(path).status_code == 401
    assert client.get("/api/crops", headers={"Authorization": "Bearer junk"}).status_code == 401


def crop_body(**kw):
    return {"crop_name": "groundnut", "sowing_date": str(date.today() - timedelta(days=40)), "location": "Kurnool",
            "land_area_acres": 2, **kw}


def test_crop_crud_and_ownership(client):
    a, b = register(client), register(client, "b@example.com")
    r = client.post("/api/crops", json=crop_body(), headers=a)
    assert r.status_code == 201
    crop = r.json()
    assert crop["crop_name"] == "Groundnut" and crop["summary"]["current_stage"]["key"] == "flowering"
    assert client.get(f"/api/crops/{crop['id']}", headers=a).status_code == 200
    assert client.get(f"/api/crops/{crop['id']}", headers=b).status_code == 404
    assert client.put(f"/api/crops/{crop['id']}", json=crop_body(variety="K6"), headers=b).status_code == 404
    assert client.delete(f"/api/crops/{crop['id']}", headers=b).status_code == 404
    assert client.put(f"/api/crops/{crop['id']}", json=crop_body(variety="K6"), headers=a).json()["variety"] == "K6"
    assert len(client.get("/api/crops", headers=b).json()) == 0
    assert client.delete(f"/api/crops/{crop['id']}", headers=a).status_code == 204


def test_crop_validation_errors(client):
    h = register(client)
    assert client.post("/api/crops", json=crop_body(crop_name="Banana"), headers=h).status_code == 422
    assert client.post("/api/crops", json=crop_body(sowing_date="2001-01-01"), headers=h).status_code == 422
    assert client.post("/api/crops", json=crop_body(land_area_acres=-1), headers=h).status_code == 422
    assert client.get("/api/crops/9999", headers=h).status_code == 404


def test_dashboard_and_notifications(client):
    h = register(client)
    client.post("/api/crops", json=crop_body(sowing_date=str(date.today() - timedelta(days=27))), headers=h)
    s = client.get("/api/dashboard/summary", headers=h).json()
    assert s["crops"][0]["crop_name"] == "Groundnut" and s["user"]["district"] == "Kurnool"
    notes = client.get("/api/notifications", headers=h).json()
    assert notes and not notes[0]["is_read"]
    assert client.put(f"/api/notifications/{notes[0]['id']}/read", headers=h).json()["is_read"] is True
    other = register(client, "c@example.com")
    assert client.put(f"/api/notifications/{notes[0]['id']}/read", headers=other).status_code == 404
