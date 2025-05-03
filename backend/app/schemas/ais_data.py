from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal

class AisDataBase(BaseModel):
    vessel_id: int
    position: str  # WKT string
    course_over_ground: Decimal
    speed_over_ground: Decimal
    rate_of_turn: Decimal
    navigation_status: int
    raw_data: str

class AisDataCreate(AisDataBase):
    pass

class AisDataResponse(AisDataBase):
    ais_data_id: int
    timestamp: datetime

    class Config:
        orm_mode = True
