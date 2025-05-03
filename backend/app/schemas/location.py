from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal

class LocationBase(BaseModel):
    vessel_id: int
    position: str  # WKT format
    accuracy_meters: Decimal
    source: str = "ais"

class LocationCreate(LocationBase):
    pass

class LocationResponse(LocationBase):
    location_id: int
    timestamp: datetime

    class Config:
        orm_mode = True
