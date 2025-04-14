from pydantic import BaseModel
from datetime import datetime

class SensorTypeBase(BaseModel):
    name: str
    description: str | None = None
    sensor_class_id: int
    manufacturer_id: int | None = None

class SensorTypeCreate(SensorTypeBase):
    pass

class SensorTypeResponse(SensorTypeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
