import pytest
from conftest import register
from app.services import market_intelligence as mi


def test_net_return_example():
    r = mi.net_return(6000, "quintal", 10, "quintal", 1000, 0)
    assert r["gross_value"] == 60000 and r["net_return"] == 59000


def test_market_comparison_example_and_ranking():
    a = {"market": "A", **mi.net_return(6000, "quintal", 10, "quintal", 1000)}
    b = {"market": "B", **mi.net_return(6300, "quintal", 10, "quintal", 2500)}
    assert (a["net_return"], b["net_return"]) == (59000, 60500)
    ranked = mi.rank_options([a, b])
    assert [o["market"] for o in ranked] == ["B", "A"] and ranked[1]["difference_vs_best"] == -1500


def test_unit_conversion_and_other_expenses():
    assert mi.net_return(60, "kg", 1000, "kg", 0, 500)["net_return"] == 59500  # Rs 6000/quintal x 10 quintal
    assert mi.net_return(60000, "tonne", 1, "tonne", 0, 0)["gross_value"] == 6000 * 10
    assert mi.to_quintals(2, "tonne") == 20


def test_unit_errors():
    with pytest.raises(mi.UnitError):
        mi.net_return(10, "bag", 1, "quintal")
    with pytest.raises(mi.UnitError):
        mi.to_quintals(1, "bale")


def test_calculate_endpoint(client):
    h = register(client)
    body = {"quantity": 10, "other_expenses": 0, "options": [
        {"market": "A", "price": 6000, "transport_cost": 1000}, {"market": "B", "price": 6300, "transport_cost": 2500}]}
    r = client.post("/api/markets/calculate", json=body, headers=h).json()
    assert r["options"][0]["market"] == "B" and r["options"][0]["net_return"] == 60500 and "disclaimer" in r
    body["quantity"] = -1
    assert client.post("/api/markets/calculate", json=body, headers=h).status_code == 422
    body.update(quantity=1, options=[{"market": "A", "price": 5, "price_unit": "bag"}])
    assert client.post("/api/markets/calculate", json=body, headers=h).status_code == 422


def test_prices_are_labelled_sample(client):
    h = register(client)
    r = client.get("/api/markets/prices", params={"crop": "Groundnut"}, headers=h).json()
    assert r["latest"] and r["is_sample_data"] and all(p["is_sample"] and "SAMPLE" in p["source"] for p in r["latest"])
    assert r["history"] and "date" in r["history"][0]
    assert client.get("/api/markets/prices", params={"crop": "Banana"}, headers=h).status_code == 422


def test_compare_endpoint_ranks_and_saves(client):
    h = register(client)
    r = client.post("/api/markets/compare", json={"crop": "Groundnut", "quantity": 10, "default_transport_cost": 500,
                                                  "transport_costs": {"Adoni": 3000}}, headers=h)
    assert r.status_code == 200
    nets = [o["net_return"] for o in r.json()["options"]]
    assert nets == sorted(nets, reverse=True) and r.json()["options"][0]["rank"] == 1
    assert len(client.get("/api/markets/history", headers=h).json()) == 1


def test_refresh_without_config_is_clear_error(client):
    assert client.post("/api/markets/refresh", headers=register(client)).status_code == 503
