from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from decimal import Decimal
from .fleet import FleetResponse
from .vessel_type import VesselTypeResponse
from .operator import OperatorResponse


class VesselLatestLocationResponse(BaseModel):
    vessel_id: int
    name: str
    latest_position_wkt: Optional[str] = None
    latest_heading: Optional[Decimal] = None
    latest_timestamp: Optional[datetime] = None

    class Config:
        from_attributes = True


class VesselBase(BaseModel):
    name: str
    vessel_type_id: int
    operator_id: int
    fleet_id: Optional[int] = None
    production_year: Optional[int] = None
    registration_number: Optional[str] = None
    imo_number: Optional[str] = None
    mmsi_number: Optional[str] = None
    call_sign: Optional[str] = None
    status: Optional[str] = Field(
        default="active", pattern="^(active|maintenance|retired|out_of_service)$"
    )


class VesselCreate(VesselBase):
    pass


class VesselResponse(VesselCreate):
    id: int

    fleet: Optional[FleetResponse] = None
    vessel_type: Optional[VesselTypeResponse] = None
    operator: Optional[OperatorResponse] = None

    class Config:
        from_attributes = True
