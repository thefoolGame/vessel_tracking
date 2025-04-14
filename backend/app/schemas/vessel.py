from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class VesselCreate(BaseModel):
    name: str
    vessel_type_id: int
    operator_id: int
    fleet_id: Optional[int] = None
    production_year: Optional[int] = None
    registration_number: Optional[str] = None
    imo_number: Optional[str] = None
    mmsi_number: Optional[str] = None
    call_sign: Optional[str] = None
    status: Optional[str] = Field(default="active", pattern="^(active|maintenance|retired|out_of_service)$")

class VesselResponse(VesselCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
