from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal

class SensorReadingBase(BaseModel):
    sensor_id: int
    value: Decimal
    status: str = "normal"

class SensorReadingCreate(SensorReadingBase):
    pass

class SensorReadingResponse(SensorReadingBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True
