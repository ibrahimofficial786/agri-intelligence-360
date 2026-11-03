import re
from datetime import date, datetime, timedelta
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegisterIn(BaseModel):
    email: str = Field(max_length=160)
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=120)
    district: str = Field(default="Kurnool", min_length=2, max_length=80)
    mandal: str | None = Field(default=None, max_length=80)
    language: Literal["en", "te"] = "en"

    @field_validator("email")
    @classmethod
    def _email(cls, v):
        v = v.strip().lower()
        if not EMAIL_RE.match(v):
            raise ValueError("Enter a valid email address")
        return v

    @field_validator("password")
    @classmethod
    def _pw(cls, v):
        if not (re.search(r"[A-Za-z]", v) and re.search(r"\d", v)):
            raise ValueError("Password needs at least one letter and one number")
        return v


class LoginIn(BaseModel):
    email: str
    password: str


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    district: str | None = Field(default=None, min_length=2, max_length=80)
    mandal: str | None = Field(default=None, max_length=80)
    language: Literal["en", "te"] | None = None


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    district: str
    mandal: str | None = None
    language: str
    is_demo: bool = False


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class CropIn(BaseModel):
    crop_name: str = Field(min_length=2, max_length=60)
    variety: str | None = Field(default=None, max_length=80)
    sowing_date: date
    location: str = Field(min_length=2, max_length=80)
    land_area_acres: float | None = Field(default=None, gt=0, le=10000)
    soil_type: str | None = Field(default=None, max_length=60)
    irrigation_method: str | None = Field(default=None, max_length=60)

    @field_validator("sowing_date")
    @classmethod
    def _sow(cls, v):
        if v < date.today() - timedelta(days=400) or v > date.today() + timedelta(days=90):
            raise ValueError("Sowing date must be within the last 400 days or the next 90 days")
        return v


class CropOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    crop_name: str
    variety: str | None
    sowing_date: date
    location: str
    land_area_acres: float | None
    soil_type: str | None
    irrigation_method: str | None
    is_demo: bool
    created_at: datetime
    summary: dict | None = None


class HealthOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    crop_id: int | None
    crop_name: str
    status: str
    predicted_label: str | None
    confidence: float | None
    result: dict
    has_image: bool = False
    is_demo: bool
    created_at: datetime


class MarketOption(BaseModel):
    market: str = Field(min_length=1, max_length=80)
    price: float = Field(gt=0)
    price_unit: Literal["quintal", "kg", "tonne"] = "quintal"
    transport_cost: float = Field(default=0, ge=0)


class CalcIn(BaseModel):
    quantity: float = Field(gt=0)
    quantity_unit: Literal["quintal", "kg", "tonne"] = "quintal"
    other_expenses: float = Field(default=0, ge=0)
    options: list[MarketOption] = Field(min_length=1, max_length=20)


class CompareIn(BaseModel):
    crop: str
    quantity: float = Field(gt=0)
    quantity_unit: Literal["quintal", "kg", "tonne"] = "quintal"
    other_expenses: float = Field(default=0, ge=0)
    default_transport_cost: float = Field(default=0, ge=0)
    transport_costs: dict[str, float] = {}
    markets: list[str] | None = None
