"""Crop calendar calculations. Stage data comes from the crop_stages table (seeded from data/crop_catalog.json)."""
from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.models import Crop, CropStage

DISCLAIMER = ("Growth-stage dates are estimates. They vary with variety, weather, season and local conditions. "
              "Doses are not given here: use soil test results and consult your local agriculture officer or KVK.")


def supported_crops(db: Session) -> list[str]:
    return list(db.scalars(select(CropStage.crop_name).distinct().order_by(CropStage.crop_name)))


def canonical_crop(db: Session, name: str) -> str | None:
    n = name.strip().lower()
    return next((c for c in supported_crops(db) if c.lower() == n), None)


def stage_defs(db: Session, crop_name: str) -> list[dict]:
    rows = db.scalars(select(CropStage).where(CropStage.crop_name == crop_name).order_by(CropStage.position))
    return [dict(key=r.stage_key, name_en=r.name_en, name_te=r.name_te, start_day=r.start_day, end_day=r.end_day,
                 activities=r.activities, irrigation=r.irrigation, nutrients=r.nutrients, monitoring=r.monitoring)
            for r in rows]


def compute_calendar(stages: list[dict], sowing_date: date, today: date | None = None) -> dict:
    """Pure function: estimate the stage for a sowing date and build the full calendar."""
    today = today or date.today()
    days = (today - sowing_date).days
    cal, current, nxt = [], None, None
    for s in stages:
        start, end = sowing_date + timedelta(days=s["start_day"]), sowing_date + timedelta(days=s["end_day"])
        if days < 0 or days < s["start_day"]:
            status = "upcoming"
        elif days < s["end_day"]:
            status = "current"
        else:
            status = "completed"
        item = {**s, "start_date": start, "end_date": end, "status": status}
        cal.append(item)
        if status == "current":
            current = item
    if days < 0:
        phase = "not_sown"
    elif current:
        phase = "growing"
    elif stages and days >= stages[-1]["end_day"]:
        phase = "past_expected_duration"
    else:
        phase = "growing"
    upcoming = [c for c in cal if c["status"] == "upcoming"]
    nxt = upcoming[0] if upcoming else None
    return {"days_since_sowing": days, "phase": phase, "current_stage": current, "next_stage": nxt,
            "days_to_next_stage": (nxt["start_date"] - today).days if nxt else None,
            "calendar": cal, "disclaimer": DISCLAIMER}


def build_guidance(db: Session, crop: Crop, today: date | None = None) -> dict:
    cal = compute_calendar(stage_defs(db, crop.crop_name), crop.sowing_date, today)
    cur, nxt = cal["current_stage"], cal["next_stage"]
    reminders = []
    if cal["phase"] == "not_sown":
        reminders.append(f"Sowing date is {-cal['days_since_sowing']} day(s) away. Prepare land and inputs.")
    if cur:
        reminders.append(f"Monitoring focus: {cur['monitoring']}")
    if nxt and cal["days_to_next_stage"] is not None and cal["days_to_next_stage"] <= 7:
        reminders.append(f"{nxt['name_en']} is expected in about {cal['days_to_next_stage']} day(s). "
                         f"Prepare for: {'; '.join(nxt['activities'][:2])}")
    if cal["phase"] == "past_expected_duration":
        reminders.append("The crop is past its typical duration. Check harvest readiness in the field.")
    return {**cal, "crop_id": crop.id, "crop_name": crop.crop_name, "reminders": reminders,
            "nutrient_note": "No fertilizer dose is listed. Base the plan on a soil test and local recommendations."}


def crop_summary(stage_map: dict[str, list[dict]], crop: Crop, today: date | None = None) -> dict:
    cal = compute_calendar(stage_map.get(crop.crop_name, []), crop.sowing_date, today)
    cur = cal["current_stage"]
    return {"days_since_sowing": cal["days_since_sowing"], "phase": cal["phase"],
            "current_stage": {"key": cur["key"], "name_en": cur["name_en"], "name_te": cur["name_te"],
                              "end_date": cur["end_date"]} if cur else None,
            "next_stage_name": cal["next_stage"]["name_en"] if cal["next_stage"] else None,
            "days_to_next_stage": cal["days_to_next_stage"]}


def load_stage_map(db: Session) -> dict[str, list[dict]]:
    return {c: stage_defs(db, c) for c in supported_crops(db)}
