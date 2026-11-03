import json
from datetime import date, timedelta
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import hash_password
from app.models.models import (Crop, CropStage, FarmerProfile, HealthReport, RiskReport, User)
from app.services.notifications import notify, sync_activity_notifications

DEMO_EMAIL, DEMO_PASSWORD = "demo@agri360.example", "Demo@12345"


def seed_catalog(db: Session):
    cat = json.loads((Path(settings.data_dir) / "crop_catalog.json").read_text(encoding="utf-8"))["crops"]
    for crop, c in cat.items():
        if db.scalar(select(CropStage.id).where(CropStage.crop_name == crop)):
            continue
        for i, s in enumerate(c["stages"]):
            db.add(CropStage(crop_name=crop, crop_name_te=c.get("name_te"), stage_key=s["key"], position=i,
                             name_en=s["name_en"], name_te=s.get("name_te"), start_day=s["start_day"],
                             end_day=s["end_day"], activities=s["activities"], irrigation=s["irrigation"],
                             nutrients=s["nutrients"], monitoring=s["monitoring"]))
    db.commit()


def seed_demo(db: Session):
    if db.scalar(select(User.id).where(User.email == DEMO_EMAIL)):
        return
    today = date.today()
    pw = hash_password(DEMO_PASSWORD)
    demo = User(email=DEMO_EMAIL, password_hash=pw, is_demo=True)
    db.add(demo); db.flush()
    db.add(FarmerProfile(user_id=demo.id, full_name="Demo Farmer", district="Kurnool", mandal="Orvakal", language="en"))
    for name, days, area, soil, irr in [("Groundnut", 42, 2.5, "Red soil", "Drip"), ("Cotton", 70, 3.0, "Black soil", "Rainfed"),
                                        ("Red gram", 20, 1.5, "Red soil", "Rainfed")]:
        db.add(Crop(user_id=demo.id, crop_name=name, sowing_date=today - timedelta(days=days), location="Kurnool",
                    land_area_acres=area, soil_type=soil, irrigation_method=irr, is_demo=True))
    db.add(HealthReport(user_id=demo.id, crop_name="Groundnut", status="demo_record", is_demo=True,
                        result={"message": "Demonstration record. It was not produced by an AI model. Spots on lower leaves were noted by the farmer.",
                                "disclaimer": "Demo data."}))
    reporters = [demo]
    for i, (area, ago) in enumerate([("Nandikotkur", 8), ("Dhone", 6), ("Kurnool", 3), ("Orvakal", 1)]):
        u = reporters[i % 3 + 1] if len(reporters) > i % 3 + 1 else None
        if u is None:
            u = User(email=f"sample{i}@agri360.example", password_hash=pw, is_demo=True)
            db.add(u); db.flush()
            db.add(FarmerProfile(user_id=u.id, full_name=f"Sample Farmer {i + 1}", district="Kurnool", language="en"))
            reporters.append(u)
        db.add(RiskReport(user_id=u.id, crop_name="Groundnut", district="Kurnool", area=area, problem="Leaf spot",
                          report_date=today - timedelta(days=ago), notes="Sample report", is_demo=True))
    db.commit()
    notify(db, demo.id, "community_risk", "Possible leaf spot risk near Kurnool (demo)",
           "Several sample reports mention groundnut leaf spot. Check your crop.", "demo-risk")
    notify(db, demo.id, "market", "Sample market prices updated", "Prices shown are demonstration data.", "demo-market")
    sync_activity_notifications(db, demo.id)
