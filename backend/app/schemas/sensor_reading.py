from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class SensorReadingBase(BaseModel):
    value: Decimal
    status: str = Field(default="normal", pattern="^(normal|warning|critical|error)$")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SensorReadingCreate(SensorReadingBase):
    pass


class SensorReadingResponse(SensorReadingBase):
    id: int
    sensor_id: int

    class Config:
        from_attributes = True
