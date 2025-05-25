from pydantic import BaseModel, validator, Field, field_validator
from datetime import datetime
from decimal import Decimal
from typing import Optional, Any
from geoalchemy2.shape import to_shape
from geoalchemy2.elements import WKBElement


class LocationBase(BaseModel):
    vessel_id: int
    position: str  # WKT format
    heading: Decimal = Field(..., ge=0, lt=360)
    accuracy_meters: Optional[Decimal] = Field(default=None, ge=0)
    source: str = Field(default="manual", pattern=r"^(ais|gps|manual|calculated)$")

    @validator("position")
    def validate_position_wkt(cls, value):
        if (
            not isinstance(value, str)
            or not value.upper().startswith("POINT (")
            or not value.endswith(")")
        ):
            raise ValueError(
                'Position must be a WKT string starting with "POINT (" and ending with ")" e.g. "POINT (10.0 20.0)"'
            )
        try:
            coords_str = value.split("(")[1].split(")")[0]
            lon, lat = map(float, coords_str.split())
            if not (-180 <= lon <= 180 and -90 <= lat <= 90):
                raise ValueError("Longitude/Latitude out of valid range.")
        except Exception:
            raise ValueError("Invalid coordinate format in WKT POINT string.")
        return value

    @validator("heading")
    def validate_heading_precision(cls, value: Decimal) -> Decimal:
        if value.as_tuple().exponent < -2:  # type: ignore
            raise ValueError("Heading can have at most 2 decimal places.")
        return value

    @validator("accuracy_meters")
    def validate_accuracy_precision(cls, value: Optional[Decimal]) -> Optional[Decimal]:
        if value is not None and value.as_tuple().exponent < -2:  # type: ignore
            raise ValueError("Accuracy can have at most 2 decimal places.")
        return value


class LocationCreate(LocationBase):
    pass


class LocationResponse(BaseModel):
    location_id: int
    vessel_id: int
    timestamp: datetime
    position: str  # WKT format, np. "POINT (lon lat)"
    heading: Decimal
    accuracy_meters: Optional[float] = None
    source: str

    @field_validator("position", mode="before")
    @classmethod
    def convert_position_to_wkt(cls, v: Any) -> Optional[str]:
        if isinstance(v, WKBElement):  # Jeśli z ORM przychodzi WKBElement
            return to_shape(v).wkt
        if isinstance(v, str):  # Jeśli już jest stringiem (np. przy tworzeniu)
            return v
        return None

    class Config:
        from_attributes = True
