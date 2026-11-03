from datetime import date
from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import current_user, owned_crop
from app.core.config import settings
from app.database.db import get_db
from app.models.models import HealthReport, User
from app.schemas.schemas import HealthOut
from app.services import crop_guidance as cg, crop_health as ch
from app.services.notifications import notify

router = APIRouter(prefix="/api/health", tags=["crop health"])


def _out(r: HealthReport) -> HealthOut:
    o = HealthOut.model_validate(r)
    o.has_image = bool(r.image_path)
    return o


async def read_validated(file: UploadFile) -> tuple[bytes, str]:
    limit = settings.max_upload_mb * 1024 * 1024
    data = await file.read(limit + 1)
    try:
        fmt, _ = ch.validate_image(data, limit)
    except ch.ImageValidationError as e:
        code = 413 if "larger" in str(e) else 415 if "Unsupported" in str(e) else 400
        raise HTTPException(code, str(e))
    return data, fmt


@router.get("/status")
def model_status(user: User = Depends(current_user)):
    c = ch.get_classifier()
    return {"model_available": c.available, "message": "" if c.available else c.reason,
            "problem_options": ch.problem_options()}


@router.post("/analyse", response_model=HealthOut, status_code=201)
async def analyse(file: UploadFile = File(...), crop_id: int | None = Form(None), crop_name: str | None = Form(None),
                  user: User = Depends(current_user), db: Session = Depends(get_db)):
    data, fmt = await read_validated(file)
    crop = owned_crop(db, user, crop_id) if crop_id else None
    name = crop.crop_name if crop else (cg.canonical_crop(db, crop_name or "") or None)
    if not name:
        raise HTTPException(422, "Select a supported crop")
    result = ch.analyse(data, name)
    report = HealthReport(user_id=user.id, crop_id=crop.id if crop else None, crop_name=name,
                          image_path=ch.save_image(data, fmt), status=result["status"],
                          predicted_label=result["predicted_label"], confidence=result["confidence"], result=result)
    db.add(report); db.commit()
    if result["status"] in ("analysed", "uncertain"):
        notify(db, user.id, "crop_health", f"Crop health report ready for {name}", result["message"], f"health:{report.id}")
    return _out(report)


@router.get("/reports", response_model=list[HealthOut])
def reports(limit: int = 20, offset: int = 0, user: User = Depends(current_user), db: Session = Depends(get_db)):
    q = select(HealthReport).where(HealthReport.user_id == user.id).order_by(HealthReport.id.desc())
    return [_out(r) for r in db.scalars(q.limit(min(limit, 100)).offset(offset))]


def _owned(db, user, rid) -> HealthReport:
    r = db.get(HealthReport, rid)
    if not r or r.user_id != user.id:
        raise HTTPException(404, "Report not found")
    return r


@router.get("/reports/{report_id}", response_model=HealthOut)
def report(report_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return _out(_owned(db, user, report_id))


@router.get("/reports/{report_id}/image")
def report_image(report_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    r = _owned(db, user, report_id)
    p = Path(settings.upload_dir) / (r.image_path or "")
    if not r.image_path or not p.exists():
        raise HTTPException(404, "Image not found")
    return FileResponse(p)
