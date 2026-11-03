from datetime import date, datetime
from sqlalchemy import (JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text,
                        UniqueConstraint, func)
from sqlalchemy.orm import Mapped, mapped_column
from app.database.db import Base


class Timestamps:
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class User(Base, Timestamps):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)


class FarmerProfile(Base, Timestamps):
    __tablename__ = "farmer_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    full_name: Mapped[str] = mapped_column(String(120))
    district: Mapped[str] = mapped_column(String(80), default="Kurnool")
    mandal: Mapped[str | None] = mapped_column(String(80))
    language: Mapped[str] = mapped_column(String(5), default="en")


class Crop(Base, Timestamps):
    __tablename__ = "crops"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    crop_name: Mapped[str] = mapped_column(String(60), index=True)
    variety: Mapped[str | None] = mapped_column(String(80))
    sowing_date: Mapped[date] = mapped_column(Date)
    location: Mapped[str] = mapped_column(String(80))
    land_area_acres: Mapped[float | None] = mapped_column(Float)
    soil_type: Mapped[str | None] = mapped_column(String(60))
    irrigation_method: Mapped[str | None] = mapped_column(String(60))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)


class CropStage(Base, Timestamps):
    """Stage definitions and recommendations, seeded from data/crop_catalog.json."""
    __tablename__ = "crop_stages"
    __table_args__ = (UniqueConstraint("crop_name", "stage_key"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    crop_name: Mapped[str] = mapped_column(String(60), index=True)
    crop_name_te: Mapped[str | None] = mapped_column(String(80))
    stage_key: Mapped[str] = mapped_column(String(40))
    position: Mapped[int] = mapped_column(Integer)
    name_en: Mapped[str] = mapped_column(String(120))
    name_te: Mapped[str | None] = mapped_column(String(120))
    start_day: Mapped[int] = mapped_column(Integer)
    end_day: Mapped[int] = mapped_column(Integer)
    activities: Mapped[list] = mapped_column(JSON, default=list)
    irrigation: Mapped[str] = mapped_column(Text, default="")
    nutrients: Mapped[str] = mapped_column(Text, default="")
    monitoring: Mapped[str] = mapped_column(Text, default="")


class HealthReport(Base, Timestamps):
    __tablename__ = "health_reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    crop_id: Mapped[int | None] = mapped_column(ForeignKey("crops.id", ondelete="SET NULL"))
    crop_name: Mapped[str] = mapped_column(String(60))
    image_path: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(30))  # analysed | uncertain | model_unavailable | demo_record
    predicted_label: Mapped[str | None] = mapped_column(String(80))
    confidence: Mapped[float | None] = mapped_column(Float)
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)


class RiskReport(Base, Timestamps):
    __tablename__ = "risk_reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    crop_name: Mapped[str] = mapped_column(String(60), index=True)
    district: Mapped[str] = mapped_column(String(80), index=True)
    area: Mapped[str | None] = mapped_column(String(80))  # mandal / general area only
    problem: Mapped[str] = mapped_column(String(80), index=True)
    notes: Mapped[str | None] = mapped_column(String(500))
    report_date: Mapped[date] = mapped_column(Date, index=True)
    photo_path: Mapped[str | None] = mapped_column(String(255))
    health_report_id: Mapped[int | None] = mapped_column(ForeignKey("health_reports.id", ondelete="SET NULL"))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)


class MarketPrice(Base, Timestamps):
    __tablename__ = "market_prices"
    __table_args__ = (UniqueConstraint("crop_name", "market", "price_date", "source"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    crop_name: Mapped[str] = mapped_column(String(60), index=True)
    market: Mapped[str] = mapped_column(String(80))
    district: Mapped[str | None] = mapped_column(String(80))
    price: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(12), default="quintal")
    price_date: Mapped[date] = mapped_column(Date, index=True)
    source: Mapped[str] = mapped_column(String(160))
    is_sample: Mapped[bool] = mapped_column(Boolean, default=True)


class MarketComparison(Base, Timestamps):
    __tablename__ = "market_comparisons"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    crop_name: Mapped[str] = mapped_column(String(60))
    quantity_quintals: Mapped[float] = mapped_column(Float)
    result: Mapped[dict] = mapped_column(JSON, default=dict)


class Notification(Base, Timestamps):
    __tablename__ = "notifications"
    __table_args__ = (UniqueConstraint("user_id", "ref_key"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(30))  # crop_activity | crop_health | community_risk | market
    title: Mapped[str] = mapped_column(String(160))
    body: Mapped[str] = mapped_column(String(500), default="")
    ref_key: Mapped[str | None] = mapped_column(String(160))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
