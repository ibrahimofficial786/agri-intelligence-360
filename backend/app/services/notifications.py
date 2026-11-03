from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.models import Crop, Notification
from app.services import crop_guidance as cg


def notify(db: Session, user_id: int, kind: str, title: str, body: str = "", ref_key: str | None = None) -> bool:
    if ref_key and db.scalar(select(Notification.id).where(Notification.user_id == user_id, Notification.ref_key == ref_key)):
        return False
    db.add(Notification(user_id=user_id, kind=kind, title=title[:160], body=body[:500], ref_key=ref_key))
    db.commit()
    return True


def sync_activity_notifications(db: Session, user_id: int):
    """Create in-app reminders for stages starting within 7 days or just started. Deduplicated by ref_key."""
    stage_map = cg.load_stage_map(db)
    for crop in db.scalars(select(Crop).where(Crop.user_id == user_id)):
        cal = cg.compute_calendar(stage_map.get(crop.crop_name, []), crop.sowing_date)
        nxt, cur = cal["next_stage"], cal["current_stage"]
        if nxt and cal["days_to_next_stage"] is not None and 0 <= cal["days_to_next_stage"] <= 7:
            notify(db, user_id, "crop_activity", f"{crop.crop_name}: {nxt['name_en']} starts soon",
                   f"Expected in about {cal['days_to_next_stage']} day(s). {nxt['activities'][0]}", f"next:{crop.id}:{nxt['key']}")
        if cur and cal["days_since_sowing"] - cur["start_day"] <= 3:
            notify(db, user_id, "crop_activity", f"{crop.crop_name}: now in {cur['name_en']}",
                   cur["monitoring"], f"start:{crop.id}:{cur['key']}")
