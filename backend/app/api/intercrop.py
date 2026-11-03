from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.api.deps import current_user
from app.models.models import User
from app.services import intercrop_engine as ie

router = APIRouter(prefix="/api/intercrop", tags=["smart intercrop"])
SOILS = ["Red soil", "Black soil", "Sandy loam", "Clay loam", "Alluvial"]


class RecommendIn(BaseModel):
    primary_crop: str = Field(min_length=2, max_length=60)
    season: Literal["kharif", "rabi", "zaid"]
    soil_type: Literal["Red soil", "Black soil", "Sandy loam", "Clay loam", "Alluvial"] | None = None
    soil_ph: float | None = Field(default=None, ge=3.5, le=9.5)
    rainfall_mm: float | None = Field(default=None, ge=0, le=5000)
    temperature_c: float | None = Field(default=None, ge=5, le=45)
    water_availability: Literal["low", "medium", "high"] | None = None
    irrigation: Literal["rainfed", "drip", "sprinkler", "canal", "borewell"] | None = None
    region: str | None = Field(default=None, max_length=80)
    limit: int = Field(default=6, ge=1, le=12)


@router.get("/crops")
def crops(user: User = Depends(current_user)):
    d = ie.load_data()
    return {"crops": [{"key": k, "name": c["name"], "name_te": c["name_te"], "group": c["group"], "seasons": c["seasons"],
                       "water": c["water"], "duration_days": c["duration"]} for k, c in d["crops"].items()]}


@router.get("/meta")
def meta(user: User = Depends(current_user)):
    d = ie.load_data()
    return {"seasons": ["kharif", "rabi", "zaid"], "soil_types": SOILS, "patterns": list(ie.PATTERNS),
            "weights": d["weights"], "thresholds": d["thresholds"], "references_to_verify": d["references_to_verify"],
            "known_systems_note": d["known_systems_note"], "data_note": d["_note"], "data_version": d["version"],
            "engine": {"type": "rule_based", "ml_model": False}, "disclaimer": ie.DISCLAIMER}


@router.post("/recommend")
def recommend(body: RecommendIn, user: User = Depends(current_user)):
    key = ie.resolve_crop(body.primary_crop)
    if not key:
        raise HTTPException(422, "Unknown crop. Use GET /api/intercrop/crops for the supported list.")
    q = ie.Query(primary=key, season=body.season, soil_type=body.soil_type, soil_ph=body.soil_ph, rainfall_mm=body.rainfall_mm,
                 temperature_c=body.temperature_c, water_availability=body.water_availability, irrigation=body.irrigation,
                 region=(body.region or "").strip() or None, limit=body.limit)
    return ie.get_recommender().recommend(q)
