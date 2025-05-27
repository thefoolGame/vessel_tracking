from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from decimal import Decimal

from .sensor_type import SensorTypeResponse


class SensorBase(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )
    sensor_type_id: int
    serial_number: Optional[str] = Field(default=None, max_length=100)
    installation_date: Optional[date] = None
    callibration_date: Optional[date] = None
    location_on_boat: Optional[str] = None
    measurement_unit: Optional[str] = None
    min_val: Optional[Decimal] = None
    max_val: Optional[Decimal] = None


class SensorCreate(SensorBase):
    pass


class SensorUpdate(BaseModel):
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    sensor_type_id: Optional[int] = None
    serial_number: Optional[str] = Field(default=None, max_length=100)
    installation_date: Optional[date] = None
    callibration_date: Optional[date] = None
    location_on_boat: Optional[str] = None
    measurement_unit: Optional[str] = None
    min_val: Optional[Decimal] = None
    max_val: Optional[Decimal] = None


class SensorResponse(SensorBase):
    id: int
    vessel_id: int
    created_at: datetime
    updated_at: datetime

    sensor_type: SensorTypeResponse

    class Config:
        from_attributes = True
