from pydantic import BaseModel
from typing import Optional
from decimal import Decimal


class VesselTypeBase(BaseModel):
    name: str
    description: Optional[str] = None
    length_meters: Optional[Decimal] = None
    width_meters: Optional[Decimal] = None
    draft_meters: Optional[Decimal] = None
    max_speed_knots: Optional[Decimal] = None


class VesselTypeCreate(VesselTypeBase):
    manufacturer_id: int


class VesselTypeResponse(VesselTypeBase):
    id: int

    class Config:
        from_attributes = True
