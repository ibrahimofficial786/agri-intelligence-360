import json
from pathlib import Path
import pytest
from conftest import register
from app.core.config import settings
from app.services import intercrop_engine as ie


def post(client, h, **kw):
    body = {"primary_crop": "groundnut", "season": "kharif", **kw}
    return client.post("/api/intercrop/recommend", json=body, headers=h)


def test_data_integrity():
    d = ie.load_data()
    assert sum(d["weights"].values()) == 100
    assert len(d["crops"]) >= 15
    for k, c in d["crops"].items():
        assert set(c["seasons"]) <= {"kharif", "rabi", "zaid"} and c["seasons"], k
        assert c["water"] in ie.LEVEL and c["canopy"] in ("low", "medium", "tall") and c["root"] in ("shallow", "medium", "deep"), k
        assert c["duration"][0] < c["duration"][1] and c["ph"][0] < c["ph"][1] and c["temp"][0] < c["temp"][1], k
    for a, b in d["known_systems"]:
        assert a in d["crops"] and b in d["crops"]
    for k in ["paddy", "groundnut", "red_gram", "black_gram", "green_gram", "maize", "cotton", "chilli", "tomato", "sugarcane"]:
        assert k in d["crops"]


def test_requires_auth_and_lists_crops(client):
    assert client.get("/api/intercrop/crops").status_code == 401
    assert client.post("/api/intercrop/recommend", json={"primary_crop": "maize", "season": "kharif"}).status_code == 401
    h = register(client)
    names = [c["name"] for c in client.get("/api/intercrop/crops", headers=h).json()["crops"]]
    assert any("Red gram" in n for n in names) and "Paddy" in names
    m = client.get("/api/intercrop/meta", headers=h).json()
    assert m["engine"]["ml_model"] is False and m["references_to_verify"]


def test_scores_are_explainable_and_sorted(client):
    h = register(client)
    r = post(client, h, soil_type="Red soil", soil_ph=6.5, temperature_c=26, water_availability="medium").json()
    recs = r["recommendations"]
    assert recs and [x["score"] for x in recs] == sorted([x["score"] for x in recs], reverse=True)
    for x in recs:
        evaluated = [c for c in x["criteria"] if c["evaluated"]]
        assert sum(c["points"] for c in evaluated) == x["points"]
        assert x["score"] == round(x["points"] / sum(c["max"] for c in evaluated) * 100)
        assert 0 <= x["score"] <= 100 and x["benefits"] and x["limitations"] and x["patterns"]["recommended"] in ie.PATTERNS
        assert all(c["note"] for c in x["criteria"])
    assert r["engine"]["type"] == "rule_based" and r["data_completeness"] == 100 and r["confidence"] == "high"


def test_known_system_flag_and_deterministic(client):
    h = register(client)
    a, b = post(client, h).json(), post(client, h).json()
    assert a == b
    rg = next(x for x in a["recommendations"] if x["companion"]["key"] == "red_gram")
    assert rg["known_system"] is True and rg["score"] >= 70


def test_gates_family_and_season(client):
    h = register(client)
    r = post(client, h, primary_crop="tomato").json()
    assert "chilli" not in [x["companion"]["key"] for x in r["recommendations"]]
    assert any(e["key"] == "chilli" and "family" in e["reason"] for e in r["excluded"])
    r = post(client, h, season="rabi").json()
    assert "red_gram" not in [x["companion"]["key"] for x in r["recommendations"]]
    assert any(e["key"] == "red_gram" for e in r["excluded"])
    r = post(client, h, primary_crop="bengal gram", season="kharif").json()
    assert r["recommendations"] == [] and r["warnings"]


def test_missing_inputs_skip_not_guess(client):
    h = register(client)
    r = post(client, h).json()
    assert r["data_completeness"] == 65 and r["confidence"] == "low" and r["warnings"]
    skipped = [c for c in r["recommendations"][0]["criteria"] if not c["evaluated"]]
    assert {c["key"] for c in skipped} == {"water_supply", "soil", "temperature", "ph"}


def test_soil_misfit_lowers_score(client):
    h = register(client)
    good = post(client, h, soil_type="Red soil").json()["recommendations"]
    bad = post(client, h, soil_type="Alluvial").json()["recommendations"]
    g = next(x for x in good if x["companion"]["key"] == "red_gram")["score"]
    b = next((x for x in bad if x["companion"]["key"] == "red_gram"), None)
    assert b is None or b["score"] < g


def test_water_derivation_is_disclosed(client):
    h = register(client)
    r = post(client, h, rainfall_mm=300).json()
    assert any("estimated" in a for a in r["assumptions"])
    r = post(client, h, irrigation="borewell").json()
    assert any("Assumed" in a for a in r["assumptions"])


def test_relay_pattern_for_staggered_pair(client):
    h = register(client)
    r = post(client, h, primary_crop="cotton").json()
    gg = next(x for x in r["recommendations"] if x["companion"]["key"] == "green_gram")
    opts = {o["key"]: o for o in gg["patterns"]["options"]}
    assert opts["relay"]["suitable"] and set(opts) == {"row", "strip", "mixed", "relay"}


@pytest.mark.parametrize("body", [
    {"season": "kharif"}, {"primary_crop": "groundnut"}, {"primary_crop": "groundnut", "season": "winter"},
    {"primary_crop": "dragonfruit", "season": "kharif"}, {"primary_crop": "groundnut", "season": "kharif", "soil_ph": 15},
    {"primary_crop": "groundnut", "season": "kharif", "rainfall_mm": -5}, {"primary_crop": "groundnut", "season": "kharif", "temperature_c": 90},
    {"primary_crop": "groundnut", "season": "kharif", "soil_type": "Moon dust"}, {"primary_crop": "", "season": "kharif"},
    {"primary_crop": "groundnut", "season": "kharif", "limit": 0}])
def test_invalid_inputs_rejected(client, body):
    h = register(client)
    r = client.post("/api/intercrop/recommend", json=body, headers=h)
    assert r.status_code == 422 and "Traceback" not in r.text


def test_name_matching_and_regional_override(client, monkeypatch):
    h = register(client)
    assert post(client, h, primary_crop="Red Gram").status_code == 200 and post(client, h, primary_crop="Paddy").status_code == 200
    d = ie.load_data()
    monkeypatch.setitem(d, "regional_overrides", [{"region": "Kurnool", "primary": "groundnut", "companion": "red_gram", "note": "test note", "source": "test source"}])
    rg = next(x for x in post(client, h, region="Kurnool").json()["recommendations"] if x["companion"]["key"] == "red_gram")
    assert rg["regional_note"]["source"] == "test source"


def test_existing_modules_still_reachable(client):
    h = register(client)
    for path in ["/api/crops", "/api/dashboard/summary", "/api/health/status", "/api/risk/alerts", "/api/markets/prices?crop=Cotton", "/api/notifications"]:
        assert client.get(path, headers=h).status_code == 200, path
