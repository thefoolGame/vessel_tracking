from pydantic import BaseModel
from typing import Optional


class FleetBase(BaseModel):
    name: str
    description: Optional[str] = None


class FleetCreate(FleetBase):
    operator_id: int


class FleetResponse(FleetBase):
    id: int

    class Config:
        from_attributes = True
