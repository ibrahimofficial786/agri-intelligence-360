import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import current_user, profile_of
from app.core.config import settings
from app.database.db import get_db
from app.models.models import MarketComparison, User
from app.schemas.schemas import CalcIn, CompareIn
from app.services import crop_guidance as cg, market_intelligence as mi
from app.services.notifications import notify

router = APIRouter(prefix="/api/markets", tags=["markets"])
log = logging.getLogger("agri360.market")


def _row(r):
    return {"crop_name": r.crop_name, "market": r.market, "district": r.district, "price": r.price, "unit": r.unit,
            "price_date": r.price_date, "source": r.source, "is_sample": r.is_sample}


@router.get("/prices")
def prices(crop: str, district: str | None = None, days: int = 30, user: User = Depends(current_user),
           db: Session = Depends(get_db)):
    c = cg.canonical_crop(db, crop)
    if not c:
        raise HTTPException(422, "Unsupported crop")
    latest = [_row(r) for r in mi.latest_prices(db, c, district)]
    return {"crop": c, "latest": latest, "history": mi.price_history(db, c, min(max(days, 1), 365)),
            "is_sample_data": any(r["is_sample"] for r in latest), "disclaimer": mi.DISCLAIMER}


@router.post("/calculate")
def calculate(body: CalcIn, user: User = Depends(current_user)):
    try:
        opts = [{"market": o.market, **mi.net_return(o.price, o.price_unit, body.quantity, body.quantity_unit,
                                                      o.transport_cost, body.other_expenses)} for o in body.options]
    except mi.UnitError as e:
        raise HTTPException(422, str(e))
    return {"options": mi.rank_options(opts), "disclaimer": mi.DISCLAIMER}


@router.post("/compare")
def compare(body: CompareIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    c = cg.canonical_crop(db, body.crop)
    if not c:
        raise HTTPException(422, "Unsupported crop")
    rows = mi.latest_prices(db, c)
    if body.markets:
        rows = [r for r in rows if r.market in body.markets]
    if not rows:
        raise HTTPException(404, "No market prices available for this crop")
    opts = []
    for r in rows:
        t = body.transport_costs.get(r.market, body.default_transport_cost)
        opts.append({"market": r.market, "price_date": r.price_date, "source": r.source, "is_sample": r.is_sample,
                     "price": r.price, "price_unit": r.unit,
                     **mi.net_return(r.price, r.unit, body.quantity, body.quantity_unit, t, body.other_expenses)})
    ranked = mi.rank_options(opts)
    result = {"crop": c, "options": ranked, "is_sample_data": any(o["is_sample"] for o in ranked), "disclaimer": mi.DISCLAIMER}
    db.add(MarketComparison(user_id=user.id, crop_name=c, quantity_quintals=ranked[0]["quantity_quintals"],
                            result=_jsonable(result)))
    db.commit()
    return result


@router.get("/history")
def comparison_history(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(MarketComparison).filter_by(user_id=user.id).order_by(MarketComparison.id.desc()).limit(10)
    return [{"id": r.id, "crop_name": r.crop_name, "quantity_quintals": r.quantity_quintals,
             "best_market": r.result["options"][0]["market"], "best_net_return": r.result["options"][0]["net_return"],
             "created_at": r.created_at} for r in rows]


@router.post("/refresh")
def refresh(user: User = Depends(current_user), db: Session = Depends(get_db)):
    if settings.market_provider != "datagov" or not settings.data_gov_api_key:
        raise HTTPException(503, "Live market data is not configured. Set MARKET_PROVIDER=datagov and DATA_GOV_API_KEY.")
    try:
        return {"added": mi.refresh_live_prices(db, cg.supported_crops(db))}
    except Exception:  # noqa: BLE001
        log.exception("Live price refresh failed")
        raise HTTPException(502, "The market data service could not be reached. Sample prices remain available.")


def _jsonable(obj):
    import json
    from fastapi.encoders import jsonable_encoder
    return json.loads(json.dumps(jsonable_encoder(obj)))
