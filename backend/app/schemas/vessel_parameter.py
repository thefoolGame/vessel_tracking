from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class VesselParameterBase(BaseModel):
    vessel_id: int
    name: str
    value: str
    unit: Optional[str]

class VesselParameterCreate(VesselParameterBase):
    pass

class VesselParameterResponse(VesselParameterBase):
    parameter_id: int
    timestamp: datetime

    class Config:
        orm_mode = True
