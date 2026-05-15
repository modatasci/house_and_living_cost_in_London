from typing import Literal
from pydantic import BaseModel, Field


BedroomCategory = Literal[
    "Room", "Studio", "One Bedroom", "Two Bedrooms", "Three Bedrooms", "Four or More Bedrooms"
]
CouncilTaxBand = Literal["A", "B", "C", "D", "E", "F", "G", "H"]
TimeBucket = Literal["rush", "off_peak", "now"]
JourneyPreference = Literal["leasttime", "leastinterchange", "leastwalking"]


class PostcodeHit(BaseModel):
    postcode: str
    borough_code: str
    borough_name: str
    lat: float | None = None
    lng: float | None = None


class Preferences(BaseModel):
    days_per_week: int = Field(5, ge=1, le=7)
    time_bucket: TimeBucket = "rush"
    modes: list[str] | None = None  # e.g. ["tube","bus","walking"]; None = all
    journey_preference: JourneyPreference = "leasttime"
    bedroom_category: BedroomCategory = "One Bedroom"
    council_tax_band: CouncilTaxBand = "D"


class OriginInput(BaseModel):
    postcode: str
    council_tax_band: CouncilTaxBand | None = None  # override prefs.council_tax_band


class CompareRequest(BaseModel):
    destination: str  # office postcode
    origins: list[OriginInput] = Field(..., min_length=1, max_length=8)
    prefs: Preferences = Preferences()


class JourneyStep(BaseModel):
    mode: str
    start: str | None = None
    end: str | None = None
    duration_minutes: int | None = None
    line: str | None = None
    summary: str | None = None


class JourneyResult(BaseModel):
    duration_minutes: int | None
    single_fare_gbp: float | None
    legs: int | None
    steps: list[JourneyStep] = []


class CostBreakdown(BaseModel):
    monthly_commute_gbp: float
    monthly_rent_gbp: float | None
    monthly_council_tax_gbp: float
    monthly_total_gbp: float


class OriginResult(BaseModel):
    origin: str
    borough_name: str | None
    journey: JourneyResult
    cost: CostBreakdown
    rent_quartiles: dict[str, float | None] | None = None
    error: str | None = None


class CompareResponse(BaseModel):
    destination: str
    results: list[OriginResult]
