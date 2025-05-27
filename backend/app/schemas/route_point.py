from pydantic import BaseModel, validator, Field, field_validator
from typing import Optional, Any
from sqlalchemy import func
from datetime import datetime
from geoalchemy2.shape import to_shape
from geoalchemy2.elements import WKBElement


class RoutePointBase(BaseModel):
    sequence_number: int
    planned_position: str = Field(..., example="POINT(14.567 54.123)")
    planned_arrival_time: Optional[datetime] = None
    planned_departure_time: Optional[datetime] = None
    status: str = Field(
        default="planned", pattern="^(planned|reached|skipped|rescheduled)$"
    )


class RoutePointCreate(RoutePointBase):
    pass


class RoutePointUpdate(BaseModel):
    sequence_number: Optional[int] = None
    planned_position: Optional[str] = Field(
        default=None, example="POINT(14.568 54.124)"
    )
    planned_arrival_time: Optional[datetime] = None
    planned_departure_time: Optional[datetime] = None
    actual_arrival_time: Optional[datetime] = None  # Dodane dla aktualizacji
    status: Optional[str] = Field(
        default=None, pattern="^(planned|reached|skipped|rescheduled)$"
    )


class RoutePointResponse(RoutePointBase):
    route_point_id: int
    vessel_id: int
    actual_arrival_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    @field_validator("planned_position", mode="before")
    @classmethod
    def convert_position_to_wkt(cls, v: Any) -> Optional[str]:
        if isinstance(v, WKBElement):  # Jeśli z ORM przychodzi WKBElement
            return to_shape(v).wkt
        if isinstance(v, str):  # Jeśli już jest stringiem (np. przy tworzeniu)
            return v
        return None

    class Config:
        from_attributes = True
