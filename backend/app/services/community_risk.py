"""Group similar farmer reports and raise a local risk alert only when enough independent reports exist."""
import re
from collections import defaultdict
from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.models import RiskReport

NOTE = "Alerts are based on suspected farmer reports. They are not confirmed diagnoses."


def slug(problem: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", problem.strip().lower()).strip("-")


def generate_alerts(db: Session, crop: str | None = None, district: str | None = None, today: date | None = None,
                    min_reports: int | None = None, window_days: int | None = None) -> list[dict]:
    today = today or date.today()
    min_reports = min_reports or settings.risk_min_reports
    window_days = window_days or settings.risk_window_days
    q = select(RiskReport).where(RiskReport.report_date >= today - timedelta(days=window_days))
    if crop:
        q = q.where(RiskReport.crop_name == crop)
    if district:
        q = q.where(RiskReport.district == district)
    groups: dict[tuple, list[RiskReport]] = defaultdict(list)
    for r in db.scalars(q):
        groups[(r.crop_name, slug(r.problem), r.district)].append(r)
    alerts = []
    for (c, p, d), rows in groups.items():
        reporters = {r.user_id for r in rows}
        if len(rows) < min_reports or len(reporters) < 2:
            continue
        dates = sorted(r.report_date for r in rows)
        areas = sorted({r.area for r in rows if r.area})
        level = "elevated" if len(rows) >= 2 * min_reports else "watch"
        alerts.append({
            "key": f"{c}:{p}:{d}", "crop_name": c, "problem": rows[0].problem, "district": d, "areas": areas,
            "report_count": len(rows), "reporter_count": len(reporters),
            "period_start": dates[0], "period_end": dates[-1], "status": "possible_risk", "level": level,
            "has_demo_reports": any(r.is_demo for r in rows),
            "explanation": (f"{len(rows)} reports from {len(reporters)} farmers mention {rows[0].problem.lower()} in {c} "
                            f"around {d} between {dates[0]} and {dates[-1]}. {NOTE}"),
        })
    return sorted(alerts, key=lambda a: -a["report_count"])
