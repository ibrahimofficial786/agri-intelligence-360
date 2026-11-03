"""Market data providers and net-return maths."""
import json, logging, math
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Protocol
import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.models import MarketPrice

log = logging.getLogger("agri360.market")
TO_QUINTAL = {"quintal": 1.0, "kg": 0.01, "tonne": 10.0}  # quantity of 1 unit expressed in quintals
DISCLAIMER = ("Actual returns depend on quality, market deductions, commissions, transport and other expenses. "
              "Prices marked sample are for demonstration only, not real market prices.")


class UnitError(ValueError):
    pass


def to_quintals(quantity: float, unit: str) -> float:
    if unit not in TO_QUINTAL:
        raise UnitError(f"Unsupported unit '{unit}'. Use quintal, kg or tonne.")
    return quantity * TO_QUINTAL[unit]


def price_per_quintal(price: float, unit: str) -> float:
    """Price quoted per <unit> to price per quintal."""
    if unit not in TO_QUINTAL:
        raise UnitError(f"Unsupported price unit '{unit}'. Use quintal, kg or tonne.")
    return price / TO_QUINTAL[unit]


def net_return(price: float, price_unit: str, quantity: float, quantity_unit: str,
               transport: float = 0.0, other: float = 0.0) -> dict:
    ppq, qq = price_per_quintal(price, price_unit), to_quintals(quantity, quantity_unit)
    gross = round(ppq * qq, 2)
    net = round(gross - transport - other, 2)
    return {"price_per_quintal": round(ppq, 2), "quantity_quintals": round(qq, 4), "gross_value": gross,
            "transport_cost": transport, "other_expenses": other, "net_return": net,
            "formula": f"{qq:g} quintal x Rs {ppq:,.0f} = Rs {gross:,.0f}; Rs {gross:,.0f} - Rs {transport:,.0f} - Rs {other:,.0f} = Rs {net:,.0f}"}


def rank_options(options: list[dict]) -> list[dict]:
    ranked = sorted(options, key=lambda o: o["net_return"], reverse=True)
    for i, o in enumerate(ranked):
        o["rank"] = i + 1
        o["difference_vs_best"] = round(o["net_return"] - ranked[0]["net_return"], 2)
    return ranked


class MarketDataProvider(Protocol):
    name: str

    def fetch(self, crop: str) -> list[dict]: ...


DATAGOV_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
DATAGOV_COMMODITY = {"Groundnut": "Groundnut", "Cotton": "Cotton", "Paddy": "Paddy(Dhan)(Common)",
                     "Red gram": "Arhar (Tur/Red Gram)(Whole)"}  # verify names against the live dataset


class DataGovProvider:
    """Agmarknet daily mandi prices via data.gov.in. Needs DATA_GOV_API_KEY. Field names should be checked against
    the live dataset; this has not been verified against the live API in this repository's test environment."""
    name = "data.gov.in (Agmarknet)"

    def fetch(self, crop: str) -> list[dict]:
        if not settings.data_gov_api_key:
            raise RuntimeError("DATA_GOV_API_KEY is not set.")
        params = {"api-key": settings.data_gov_api_key, "format": "json", "limit": 200,
                  "filters[state.keyword]": "Andhra Pradesh", "filters[commodity]": DATAGOV_COMMODITY.get(crop, crop)}
        r = httpx.get(DATAGOV_URL, params=params, timeout=15)
        r.raise_for_status()
        out = []
        for rec in r.json().get("records", []):
            try:
                d = datetime.strptime(rec["arrival_date"], "%d/%m/%Y").date()
                out.append({"crop_name": crop, "market": rec["market"], "district": rec.get("district"),
                            "price": float(rec["modal_price"]), "unit": "quintal", "price_date": d,
                            "source": self.name, "is_sample": False})
            except (KeyError, ValueError):
                continue
        return out


def refresh_live_prices(db: Session, crops: list[str]) -> int:
    provider = DataGovProvider()
    added = 0
    for crop in crops:
        for row in provider.fetch(crop):
            exists = db.scalar(select(MarketPrice.id).where(
                MarketPrice.crop_name == crop, MarketPrice.market == row["market"],
                MarketPrice.price_date == row["price_date"], MarketPrice.source == row["source"]))
            if not exists:
                db.add(MarketPrice(**row))
                added += 1
    db.commit()
    return added


def latest_prices(db: Session, crop: str, district: str | None = None) -> list[MarketPrice]:
    """Latest price per market. Real rows win over sample rows when both exist for a market."""
    q = select(MarketPrice).where(MarketPrice.crop_name == crop)
    rows = list(db.scalars(q.order_by(MarketPrice.price_date.desc())))
    best: dict[str, MarketPrice] = {}
    for r in rows:
        cur = best.get(r.market)
        if cur is None or (cur.is_sample and not r.is_sample) or (cur.is_sample == r.is_sample and r.price_date > cur.price_date):
            best[r.market] = r
    out = sorted(best.values(), key=lambda r: (r.district != district if district else False, r.market))
    return out


def price_history(db: Session, crop: str, days: int = 30) -> list[dict]:
    since = date.today() - timedelta(days=days)
    rows = db.scalars(select(MarketPrice).where(MarketPrice.crop_name == crop, MarketPrice.price_date >= since)
                      .order_by(MarketPrice.price_date))
    by_date: dict[str, dict] = {}
    for r in rows:
        by_date.setdefault(r.price_date.isoformat(), {"date": r.price_date.isoformat()})[r.market] = r.price
    return list(by_date.values())


def seed_market_samples(db: Session):
    if db.scalar(select(func.count(MarketPrice.id)).where(MarketPrice.is_sample.is_(True))):
        return
    cfg = json.loads((Path(settings.data_dir) / "market_sample.json").read_text(encoding="utf-8"))
    today = date.today()
    for crop, c in cfg["crops"].items():
        for market, off in c["markets"].items():
            for d in range(30, -1, -2):
                wave = round(80 * math.sin((d + len(market)) / 4.0))
                db.add(MarketPrice(crop_name=crop, market=market, district="Kurnool", unit="quintal",
                                   price=float(c["base"] + off + wave), price_date=today - timedelta(days=d),
                                   source=cfg["source"], is_sample=True))
    db.commit()
