from datetime import date
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import current_user, profile_of
from app.api.health import read_validated
from app.database.db import get_db
from app.models.models import FarmerProfile, HealthReport, RiskReport, User
from app.services import crop_guidance as cg, crop_health as ch
from app.services.community_risk import generate_alerts, slug
from app.services.notifications import notify
from app.models.models import Crop

router = APIRouter(prefix="/api/risk", tags=["community risk"])


@router.post("/reports", status_code=201)
async def submit(crop_name: str = Form(...), district: str = Form(...), area: str | None = Form(None),
                 report_date: date = Form(...), problem: str = Form(...), notes: str | None = Form(None),
                 health_report_id: int | None = Form(None), photo: UploadFile | None = File(None),
                 user: User = Depends(current_user), db: Session = Depends(get_db)):
    crop = cg.canonical_crop(db, crop_name)
    if not crop:
        raise HTTPException(422, "Select a supported crop")
    if report_date > date.today():
        raise HTTPException(422, "Report date cannot be in the future")
    problem = problem.strip()
    if len(problem) < 2 or len(problem) > 80 or len(district.strip()) < 2:
        raise HTTPException(422, "Enter the problem and district")
    if health_report_id:
        h = db.get(HealthReport, health_report_id)
        if not h or h.user_id != user.id:
            raise HTTPException(404, "Health report not found")
    path = None
    if photo is not None and photo.filename:
        data, fmt = await read_validated(photo)
        path = ch.save_image(data, fmt)
    r = RiskReport(user_id=user.id, crop_name=crop, district=district.strip(), area=(area or "").strip() or None,
                   problem=problem, notes=(notes or "")[:500] or None, report_date=report_date, photo_path=path,
                   health_report_id=health_report_id)
    db.add(r); db.commit()
    alerts = [a for a in generate_alerts(db, crop, r.district) if a["key"].split(":")[1] == slug(problem)]
    if alerts:
        a = alerts[0]
        peers = db.scalars(select(Crop.user_id).join(FarmerProfile, FarmerProfile.user_id == Crop.user_id)
                           .where(Crop.crop_name == crop, FarmerProfile.district == r.district).distinct())
        for uid in peers:
            notify(db, uid, "community_risk", f"Possible {a['problem'].lower()} risk for {crop} near {a['district']}",
                   a["explanation"], f"risk:{a['key']}:{a['level']}")
    return {"id": r.id, "status": "suspected_report_saved", "alert_triggered": bool(alerts),
            "note": "Saved as a suspected report. It is not a confirmed diagnosis."}


@router.get("/alerts")
def alerts(crop: str | None = None, district: str | None = None, user: User = Depends(current_user),
           db: Session = Depends(get_db)):
    return {"alerts": generate_alerts(db, crop, district or profile_of(db, user).district),
            "note": "Alerts are based on suspected farmer reports, not confirmed diagnoses."}


@router.get("/reports/mine")
def mine(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(RiskReport).where(RiskReport.user_id == user.id).order_by(RiskReport.id.desc()).limit(50))
    return [{"id": r.id, "crop_name": r.crop_name, "problem": r.problem, "district": r.district, "area": r.area,
             "report_date": r.report_date, "is_demo": r.is_demo, "type": "suspected"} for r in rows]
