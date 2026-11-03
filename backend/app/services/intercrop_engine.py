"""SMART INTERCROP: explainable, rule-based intercropping recommender.

Every score is the sum of named criteria (weights in data/intercrop_data.json). Missing optional inputs are
skipped, not guessed, and the score is rescaled over the criteria that could be evaluated. This is NOT machine
learning. To add an ML model later, implement `Recommender` and return it from `get_recommender()`."""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from app.core.config import settings

LEVEL = {"low": 1, "medium": 2, "high": 3}
PATTERNS = ("row", "strip", "mixed", "relay")
DISCLAIMER = ("Rule-based guidance from approximate, unverified crop traits. It is not a yield or profit prediction. "
              "Confirm crop choice, row ratios, varieties and seed rates with ANGRAU, your KVK or a local agriculture officer.")
_data: dict | None = None


def load_data(reload: bool = False) -> dict:
    global _data
    if _data is None or reload:
        _data = json.loads((Path(settings.data_dir) / "intercrop_data.json").read_text(encoding="utf-8"))
    return _data


@dataclass
class Query:
    primary: str
    season: str
    soil_type: str | None = None
    soil_ph: float | None = None
    rainfall_mm: float | None = None
    temperature_c: float | None = None
    water_availability: str | None = None
    irrigation: str | None = None
    region: str | None = None
    limit: int = 6


class Recommender(Protocol):
    def recommend(self, q: Query) -> dict: ...


def resolve_crop(text: str) -> str | None:
    t = (text or "").strip().lower()
    for key, c in load_data()["crops"].items():
        if t in (key, c["name"].lower(), key.replace("_", " ")) or t == c["name"].split(" (")[0].lower():
            return key
    return None


def _mid(c): return sum(c["duration"]) / 2


def derive_water(q: Query) -> tuple[str | None, str | None]:
    if q.water_availability:
        return q.water_availability, None
    level, note = None, None
    if q.rainfall_mm is not None:
        level = "low" if q.rainfall_mm < 500 else "medium" if q.rainfall_mm < 900 else "high"
        note = f"Water availability was estimated as '{level}' from the rainfall you entered."
    if q.irrigation and q.irrigation != "rainfed":
        if level in (None, "low"):
            level, note = "medium", "Assumed 'medium' water availability because an irrigation source was selected. Enter water availability for better accuracy."
    return level, note


# ---- criteria: each returns (points, max, note) or None when the needed input is missing ----
def c_nitrogen(p, c, q, w):
    if c["legume"] and not p["legume"]:
        return w, w, f"{c['name']} is a legume, which can fix atmospheric nitrogen, so it complements a non-legume main crop."
    if p["legume"] and not c["legume"]:
        return round(w * .5), w, f"{p['name']} is a legume; {c['name']} is not, so there is some nitrogen complementarity."
    if p["legume"] and c["legume"]:
        return round(w * .33), w, "Both are legumes, so there is little nitrogen complementarity."
    return round(w * .27), w, "Neither crop is a legume, so there is no nitrogen complementarity."


def c_canopy(p, c, q, w):
    a, b = sorted([p["canopy"], c["canopy"]], key=["low", "medium", "tall"].index)
    pts = {("low", "tall"): 1.0, ("medium", "tall"): .8, ("low", "medium"): .8, ("tall", "tall"): .2}.get((a, b), .33)
    note = (f"Canopy heights differ ({p['canopy']} vs {c['canopy']}), so the crops can share light." if a != b
            else f"Both crops have a {a} canopy, so they compete for light.")
    return round(w * pts), w, note


def c_duration(p, c, q, w):
    ratio = _mid(c) / _mid(p)
    if ratio <= .7 or ratio >= 1.3:
        shorter = c["name"] if ratio < 1 else p["name"]
        return w, w, f"Durations are staggered (about {round(_mid(p))} vs {round(_mid(c))} days); {shorter} finishes first, which spreads competition and harvests."
    return round(w * .53), w, "Durations are similar, so both crops need resources at the same time."


def c_root(p, c, q, w):
    d = {p["root"], c["root"]}
    if d == {"shallow", "deep"}:
        return w, w, "Shallow and deep roots draw from different soil layers."
    if p["root"] != c["root"]:
        return round(w * .7), w, "Rooting depths differ somewhat."
    return round(w * .4), w, f"Both crops have {p['root']} roots and draw from the same soil layer."


def c_water_pair(p, c, q, w):
    d = abs(LEVEL[p["water"]] - LEVEL[c["water"]])
    pts = {0: 1.0, 1: .6, 2: 0}[d]
    note = "Water needs are similar." if d == 0 else "Water needs differ by one level." if d == 1 else "Water needs are very different (low vs high), which makes joint irrigation hard."
    return round(w * pts), w, note


def c_water_supply(p, c, q, w):
    level, _ = derive_water(q)
    if level is None:
        return None
    need = max(LEVEL[p["water"]], LEVEL[c["water"]])
    short = max(0, need - LEVEL[level])
    pts = {0: 1.0, 1: .4, 2: 0}[short]
    return round(w * pts), w, (f"Water availability ({level}) meets the needs of both crops." if short == 0 else
                               f"Water availability ({level}) is below what the thirstier crop needs.")


def c_soil(p, c, q, w):
    if not q.soil_type:
        return None
    n = (q.soil_type in p["soils"]) + (q.soil_type in c["soils"])
    return round(w * (n / 2)), w, {2: f"{q.soil_type} suits both crops.", 1: f"{q.soil_type} suits only one of the crops.",
                                  0: f"{q.soil_type} is not typical for either crop."}[n]


def c_temp(p, c, q, w):
    if q.temperature_c is None:
        return None
    n = sum(c_["temp"][0] <= q.temperature_c <= c_["temp"][1] for c_ in (p, c))
    return round(w * (n / 2)), w, {2: f"{q.temperature_c:g} °C is within the range of both crops.", 1: f"{q.temperature_c:g} °C is within the range of only one crop.",
                                   0: f"{q.temperature_c:g} °C is outside the usual range of both crops."}[n]


def c_ph(p, c, q, w):
    if q.soil_ph is None:
        return None
    n = sum(c_["ph"][0] <= q.soil_ph <= c_["ph"][1] for c_ in (p, c))
    return round(w * (n / 2)), w, {2: f"pH {q.soil_ph:g} suits both crops.", 1: f"pH {q.soil_ph:g} suits only one crop.",
                                   0: f"pH {q.soil_ph:g} is outside the usual range of both crops."}[n]


CRITERIA = [("nitrogen", "Nitrogen complementarity", c_nitrogen), ("canopy", "Light sharing (canopy)", c_canopy),
            ("duration", "Duration fit", c_duration), ("root", "Root zones", c_root),
            ("water_pair", "Water need match", c_water_pair), ("water_supply", "Water supply", c_water_supply),
            ("soil", "Soil type", c_soil), ("temperature", "Temperature", c_temp), ("ph", "Soil pH", c_ph)]


def score_pair(p, c, q, weights) -> dict:
    rows, earned, possible = [], 0, 0
    for key, label, fn in CRITERIA:
        r = fn(p, c, q, weights[key])
        if r is None:
            rows.append({"key": key, "label": label, "points": None, "max": weights[key], "note": "Not evaluated: input not provided.", "evaluated": False})
            continue
        pts, mx, note = r
        earned, possible = earned + pts, possible + mx
        rows.append({"key": key, "label": label, "points": pts, "max": mx, "note": note, "evaluated": True})
    return {"criteria": rows, "earned": earned, "possible": possible,
            "score": round(earned / possible * 100) if possible else 0}


def patterns_for(p, c, q) -> dict:
    ratio = _mid(c) / _mid(p)
    staggered = ratio <= .7 or ratio >= 1.3
    wdiff = abs(LEVEL[p["water"]] - LEVEL[c["water"]])
    canopy_diff, root_diff = p["canopy"] != c["canopy"], p["root"] != c["root"]
    first = c["name"] if ratio < 1 else p["name"]
    out = {
        "row": (canopy_diff or root_diff, "Alternate rows or row sets let each crop get its own space and light. Best when canopy or root depth differs."
                if (canopy_diff or root_diff) else "Both crops are similar in canopy and roots, so competition within rows is likely."),
        "strip": (wdiff >= 1 or staggered, "Separate strips make it easier to irrigate, weed and harvest crops that differ in water need or timing."
                  if (wdiff >= 1 or staggered) else "Crops are alike in water need and timing, so separate strips add little."),
        "mixed": (not staggered and wdiff == 0 and not (p["canopy"] == c["canopy"] == "tall"),
                  "Similar duration and water need make mixing seeds workable for low-input rainfed fields."
                  if (not staggered and wdiff == 0) else "Different duration or water need makes a random mix hard to manage."),
        "relay": (staggered, f"Staggered durations allow sowing the second crop before the first is harvested ({first} finishes first)."
                  if staggered else "Durations are too similar for relay sowing."),
    }
    rec = next((k for k in ("row", "strip", "mixed", "relay") if out[k][0]), "row")
    return {"recommended": rec, "options": [{"key": k, "suitable": out[k][0], "reason": out[k][1]} for k in PATTERNS]}


def benefits_and_limits(p, c, q, scored, pat) -> tuple[list, list]:
    ben, lim = [], []
    if c["legume"] and not p["legume"]:
        ben.append("Legumes can fix atmospheric nitrogen, which may reduce the nitrogen needed later. The size of the effect depends on variety and management and is not quantified here.")
    if p["canopy"] != c["canopy"]:
        ben.append("Different canopy heights allow better use of sunlight.")
    if p["root"] != c["root"]:
        ben.append("Different rooting depths use water and nutrients from different soil layers.")
    if _mid(c) / _mid(p) <= .7 or _mid(c) / _mid(p) >= 1.3:
        ben.append("Staggered durations spread labour and give two harvests at different times.")
    if c["canopy"] == "low" and p["canopy"] != "low":
        ben.append("A low-growing companion covers the soil and may help reduce weed growth. The effect varies.")
    ben.append("Two crops on one field spread market and weather risk compared with a single crop.")
    if p["family"] == c["family"]:
        lim.append("Crops share a botanical family, so shared pests and diseases are possible.")
    if abs(LEVEL[p["water"]] - LEVEL[c["water"]]) == 2:
        lim.append("Water needs are very different; irrigating both well is difficult.")
    if p["canopy"] == c["canopy"] == "tall":
        lim.append("Two tall crops can shade each other.")
    if 0.7 < _mid(c) / _mid(p) < 1.3:
        lim.append("Similar duration means peak demand for water and nutrients overlaps.")
    if _mid(c) / _mid(p) >= 2.5 or _mid(c) / _mid(p) <= 0.4:
        lim.append("The durations differ very widely, so the longer crop occupies the field long after the shorter one is harvested. Check whether growing them in sequence is more practical.")
    if _mid(c) / _mid(p) >= 1.3:
        lim.append(f"{c['name']} stays in the field after {p['name']} is harvested; take care not to damage it during harvest.")
    for row in scored["criteria"]:
        if row["evaluated"] and row["max"] and row["points"] / row["max"] <= .4 and row["key"] in ("soil", "temperature", "ph", "water_supply"):
            lim.append(row["note"])
    if p["legume"] and c["legume"]:
        lim.append("Both legumes can host similar pests (for example pod borers), so monitor both.")
    lim.append("Row ratio, seed rate and variety are not given here: confirm them with ANGRAU or your KVK.")
    return ben, lim


class RuleBasedRecommender:
    def recommend(self, q: Query) -> dict:
        d = load_data()
        crops, weights = d["crops"], d["weights"]
        p = crops[q.primary]
        known = {frozenset(s) for s in d["known_systems"]}
        assumptions, warnings = [], []
        water_level, water_note = derive_water(q)
        if water_note:
            assumptions.append(water_note)
        out = {"primary_crop": {"key": q.primary, "name": p["name"], "name_te": p["name_te"]}, "season": q.season,
               "engine": {"type": "rule_based", "ml_model": False, "data_version": d["version"]},
               "assumptions": assumptions, "warnings": warnings, "recommendations": [], "excluded": [],
               "disclaimer": DISCLAIMER, "references_to_verify": d["references_to_verify"], "data_note": d["_note"]}
        if q.season not in p["seasons"]:
            warnings.append(f"{p['name']} is not typically grown in {q.season}. Typical seasons: {', '.join(p['seasons'])}.")
            return {**out, "data_completeness": 0, "confidence": "low"}
        results, possible_seen = [], 0
        for key, c in crops.items():
            if key == q.primary:
                continue
            if q.season not in c["seasons"]:
                out["excluded"].append({"key": key, "name": c["name"], "reason": f"Not typically grown in {q.season}."})
                continue
            if p["family"] == c["family"] and p["family"] != "Fabaceae":
                out["excluded"].append({"key": key, "name": c["name"], "reason": f"Same botanical family ({p['family']}): shared pests, diseases and nutrient demand."})
                continue
            sc = score_pair(p, c, q, weights)
            possible_seen = sc["possible"]
            pat = patterns_for(p, c, q)
            ben, lim = benefits_and_limits(p, c, q, sc, pat)
            thr = d["thresholds"]
            rating = "highly_suitable" if sc["score"] >= thr["highly_suitable"] else "suitable" if sc["score"] >= thr["suitable"] else "marginal" if sc["score"] >= thr["marginal"] else None
            if rating is None:
                out["excluded"].append({"key": key, "name": c["name"], "reason": f"Compatibility score {sc['score']} is below the minimum of {thr['marginal']}."})
                continue
            reg = next((r for r in d["regional_overrides"] if q.region and r["region"].lower() == q.region.lower()
                        and {r["primary"], r["companion"]} == {q.primary, key}), None)
            results.append({
                "companion": {"key": key, "name": c["name"], "name_te": c["name_te"], "group": c["group"]},
                "score": sc["score"], "rating": rating, "criteria": sc["criteria"], "points": sc["earned"], "points_possible": sc["possible"],
                "season": q.season, "seasons": c["seasons"], "water": {"primary": p["water"], "companion": c["water"]},
                "duration_days": {"primary": p["duration"], "companion": c["duration"]},
                "patterns": pat, "benefits": ben, "limitations": lim,
                "known_system": frozenset([q.primary, key]) in known,
                "regional_note": {"note": reg["note"], "source": reg["source"]} if reg else None,
            })
        results.sort(key=lambda r: (-r["score"], not r["known_system"], r["companion"]["name"]))
        results = results[:q.limit]
        for i, r in enumerate(results):
            r["rank"] = i + 1
        completeness = possible_seen or sum(weights[k] for k in ("nitrogen", "canopy", "duration", "root", "water_pair"))
        out.update(recommendations=results, data_completeness=completeness,
                   confidence="high" if completeness >= 90 else "medium" if completeness >= 75 else "low")
        if completeness < 90:
            warnings.append("Some inputs were not provided (soil type, pH, temperature, water). Those checks were skipped, so the ranking is less reliable.")
        if not results:
            warnings.append("No suitable companion crops were found for these inputs.")
        return out


def get_recommender() -> Recommender:
    return RuleBasedRecommender()
