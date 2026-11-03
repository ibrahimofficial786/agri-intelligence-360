from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import current_user, owned_crop
from app.database.db import get_db
from app.models.models import Crop, User
from app.schemas.schemas import CropIn, CropOut
from app.services import crop_guidance as cg
from app.services.notifications import notify, sync_activity_notifications

router = APIRouter(prefix="/api", tags=["crops"])


def _out(crop: Crop, stage_map) -> CropOut:
    out = CropOut.model_validate(crop)
    out.summary = cg.crop_summary(stage_map, crop)
    return out


def _canon(db, name):
    c = cg.canonical_crop(db, name)
    if not c:
        raise HTTPException(422, f"Unsupported crop. Supported: {', '.join(cg.supported_crops(db))}")
    return c


@router.get("/crops/catalog")
def catalog(db: Session = Depends(get_db)):
    return {"crops": cg.supported_crops(db)}


@router.get("/crops", response_model=list[CropOut])
def list_crops(limit: int = 50, offset: int = 0, user: User = Depends(current_user), db: Session = Depends(get_db)):
    sm = cg.load_stage_map(db)
    rows = db.scalars(select(Crop).where(Crop.user_id == user.id).order_by(Crop.sowing_date.desc())
                      .limit(min(limit, 100)).offset(offset))
    return [_out(c, sm) for c in rows]


@router.post("/crops", response_model=CropOut, status_code=201)
def create_crop(body: CropIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    data = body.model_dump()
    data["crop_name"] = _canon(db, body.crop_name)
    crop = Crop(user_id=user.id, **data)
    db.add(crop); db.commit()
    sync_activity_notifications(db, user.id)
    return _out(crop, cg.load_stage_map(db))


@router.get("/crops/{crop_id}", response_model=CropOut)
def get_crop(crop_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return _out(owned_crop(db, user, crop_id), cg.load_stage_map(db))


@router.put("/crops/{crop_id}", response_model=CropOut)
def update_crop(crop_id: int, body: CropIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    crop = owned_crop(db, user, crop_id)
    data = body.model_dump()
    data["crop_name"] = _canon(db, body.crop_name)
    for k, v in data.items():
        setattr(crop, k, v)
    db.commit()
    return _out(crop, cg.load_stage_map(db))


@router.delete("/crops/{crop_id}", status_code=204)
def delete_crop(crop_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(owned_crop(db, user, crop_id)); db.commit()
    return Response(status_code=204)


@router.get("/guidance/{crop_id}")
def guidance(crop_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return cg.build_guidance(db, owned_crop(db, user, crop_id))


@router.get("/crop-calendar/{crop_id}")
def calendar(crop_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    crop = owned_crop(db, user, crop_id)
    cal = cg.compute_calendar(cg.stage_defs(db, crop.crop_name), crop.sowing_date)
    return {"crop_id": crop.id, "crop_name": crop.crop_name, **cal}
