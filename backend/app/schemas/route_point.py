from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class RoutePointBase(BaseModel):
    vessel_id: int
    sequence_number: int
    planned_position: str
    planned_arrival_time: Optional[datetime] = None
    planned_departure_time: Optional[datetime] = None
    actual_arrival_time: Optional[datetime] = None
    status: str = "planned"

class RoutePointCreate(RoutePointBase):
    pass

class RoutePointResponse(RoutePointBase):
    route_point_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
