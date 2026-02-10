"""Pydantic models for auto24.ee listing data."""

from pydantic import BaseModel


class SearchResultItem(BaseModel):
    """One row from the search results page — minimal data."""

    id: str
    url: str
    title: str
    price_eur: int | None = None
    year: int | None = None
    mileage_km: int | None = None
    fuel_type: str | None = None
    transmission: str | None = None


class Listing(BaseModel):
    """Full data from an individual listing page."""

    id: str
    url: str
    make: str | None = None
    model: str | None = None
    year: int | None = None
    price_eur: int | None = None
    mileage_km: int | None = None
    fuel_type: str | None = None
    transmission: str | None = None
    engine_cc: int | None = None
    power_kw: int | None = None
    body_type: str | None = None
    drivetrain: str | None = None
    color: str | None = None
    location: str | None = None
    seller_type: str | None = None
    seller_name: str | None = None
    seller_phone: str | None = None
    description: str | None = None
    photo_urls: list[str] = []
    raw_html: str = ""
