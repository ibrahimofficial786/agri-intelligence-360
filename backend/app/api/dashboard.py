from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.api.auth import user_out
from app.api.deps import current_user
from app.database.db import get_db
from app.models.models import Crop, HealthReport, Notification, User
from app.services import crop_guidance as cg, market_intelligence as mi
from app.services.community_risk import generate_alerts
from app.services.notifications import sync_activity_notifications

router = APIRouter(prefix="/api", tags=["dashboard", "notifications"])


@router.get("/dashboard/summary")
def summary(user: User = Depends(current_user), db: Session = Depends(get_db)):
    sync_activity_notifications(db, user.id)
    me = user_out(db, user)
    sm = cg.load_stage_map(db)
    crops = list(db.scalars(select(Crop).where(Crop.user_id == user.id).order_by(Crop.sowing_date.desc())))
    crop_cards, upcoming = [], []
    for c in crops:
        cal = cg.compute_calendar(sm.get(c.crop_name, []), c.sowing_date)
        crop_cards.append({"id": c.id, "crop_name": c.crop_name, "location": c.location, "sowing_date": c.sowing_date,
                           "is_demo": c.is_demo, **cg.crop_summary(sm, c)})
        for s in cal["calendar"]:
            if s["status"] in ("current", "upcoming") and (s["start_date"] - date.today()).days <= 21:
                upcoming.append({"crop_id": c.id, "crop_name": c.crop_name, "stage": s["name_en"], "stage_te": s["name_te"],
                                 "status": s["status"], "start_date": s["start_date"],
                                 "activity": s["activities"][0] if s["activities"] else ""})
    upcoming.sort(key=lambda u: u["start_date"])
    reports = db.scalars(select(HealthReport).where(HealthReport.user_id == user.id).order_by(HealthReport.id.desc()).limit(3))
    prices = []
    for name in sorted({c.crop_name for c in crops}):
        for r in mi.latest_prices(db, name, me.district)[:2]:
            prices.append({"crop_name": r.crop_name, "market": r.market, "price": r.price, "unit": r.unit,
                           "price_date": r.price_date, "source": r.source, "is_sample": r.is_sample})
    alerts = generate_alerts(db, None, me.district)
    my_crops = {c.crop_name for c in crops}
    unread = db.scalar(select(func.count(Notification.id)).where(Notification.user_id == user.id, Notification.is_read.is_(False)))
    return {"user": me, "crops": crop_cards, "upcoming_activities": upcoming[:8],
            "recent_health_reports": [{"id": r.id, "crop_name": r.crop_name, "status": r.status, "is_demo": r.is_demo,
                                       "predicted_label": r.predicted_label, "confidence": r.confidence,
                                       "created_at": r.created_at} for r in reports],
            "latest_prices": prices, "alerts": [a for a in alerts if a["crop_name"] in my_crops] or alerts[:2],
            "unread_notifications": unread,
            "has_demo_data": any(c["is_demo"] for c in crop_cards) or any(p["is_sample"] for p in prices)}


@router.get("/notifications")
def notifications(limit: int = 30, offset: int = 0, user: User = Depends(current_user), db: Session = Depends(get_db)):
    sync_activity_notifications(db, user.id)
    rows = db.scalars(select(Notification).where(Notification.user_id == user.id).order_by(Notification.id.desc())
                      .limit(min(limit, 100)).offset(offset))
    return [{"id": n.id, "kind": n.kind, "title": n.title, "body": n.body, "is_read": n.is_read,
             "created_at": n.created_at} for n in rows]


@router.put("/notifications/{notification_id}/read")
def mark_read(notification_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    from fastapi import HTTPException
    n = db.get(Notification, notification_id)
    if not n or n.user_id != user.id:
        raise HTTPException(404, "Notification not found")
    n.is_read = True
    db.commit()
    return {"id": n.id, "is_read": True}
