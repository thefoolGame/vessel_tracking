from pydantic import BaseModel
from datetime import date, datetime
from decimal import Decimal

class SensorBase(BaseModel):
    name: str
    sensor_type_id: int
    vessel_id: int
    serial_number: str | None = None
    installation_date: date | None = None
    callibration_date: date | None = None
    location_on_boat: str | None = None
    measurement_unit: str | None = None
    min_val: Decimal | None = None
    max_val: Decimal | None = None

class SensorCreate(SensorBase):
    pass

class SensorResponse(SensorBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
