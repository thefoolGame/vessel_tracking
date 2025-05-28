from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from .route_point import RoutePointResponse


class PublicVesselMapData(BaseModel):
    vessel_id: int
    name: str
    latest_position_wkt: Optional[str] = None
    latest_heading: Optional[Decimal] = None
    latest_timestamp: Optional[datetime] = None
    planned_route: List[RoutePointResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True
