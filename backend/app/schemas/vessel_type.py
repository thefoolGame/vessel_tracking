from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from .manufacturer import ManufacturerResponse  # Załóżmy, że masz ten schemat
from .sensor_class import SensorClassResponse  # Załóżmy, że masz ten schemat


class VesselTypeBase(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    manufacturer_id: int  # Będzie wybierane z dropdown
    length_meters: Optional[Decimal] = Field(default=None, ge=0)
    width_meters: Optional[Decimal] = Field(default=None, ge=0)
    draft_meters: Optional[Decimal] = Field(default=None, ge=0)
    max_speed_knots: Optional[Decimal] = Field(default=None, ge=0)


class VesselTypeCreate(VesselTypeBase):
    pass


class VesselTypeUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    description: Optional[str] = None
    manufacturer_id: Optional[int] = None
    length_meters: Optional[Decimal] = Field(default=None, ge=0)
    width_meters: Optional[Decimal] = Field(default=None, ge=0)
    draft_meters: Optional[Decimal] = Field(default=None, ge=0)
    max_speed_knots: Optional[Decimal] = Field(default=None, ge=0)


# Schemat do reprezentowania pojedynczego wymagania czujnika
class VesselTypeSensorRequirementBase(BaseModel):
    sensor_class_id: int
    required: bool = True
    quantity: int = Field(default=1, ge=1)


class VesselTypeSensorRequirementCreate(VesselTypeSensorRequirementBase):
    pass


class VesselTypeSensorRequirementUpdate(
    BaseModel
):  # Do aktualizacji istniejącego wymagania
    required: Optional[bool] = None
    quantity: Optional[int] = Field(default=None, ge=1)


class VesselTypeSensorRequirementResponse(VesselTypeSensorRequirementBase):
    sensor_class: SensorClassResponse  # Zagnieżdżone dane klasy czujnika
    # Można dodać vessel_type_id, jeśli potrzebne

    class Config:
        from_attributes = True


class VesselTypeResponse(VesselTypeBase):
    id: int
    manufacturer: Optional[ManufacturerResponse] = None  # Zagnieżdżone dane producenta
    # Na razie nie będziemy zwracać required_sensor_classes bezpośrednio tutaj,
    # bo będzie osobny endpoint do zarządzania nimi.
    # Jeśli chcesz je tu widzieć (tylko do odczytu), można dodać:
    # required_sensor_classes: List[SensorClassResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
