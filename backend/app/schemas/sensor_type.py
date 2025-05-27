from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from .sensor_class import SensorClassResponse
from .manufacturer import ManufacturerResponse


class SensorTypeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    sensor_class_id: int  # ID wybranej klasy czujnika
    manufacturer_id: Optional[int] = (
        None  # ID wybranego producenta (może być opcjonalny)
    )


class SensorTypeCreate(SensorTypeBase):
    pass


class SensorTypeUpdate(
    BaseModel
):  # Osobna klasa dla aktualizacji, wszystkie pola opcjonalne
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None
    sensor_class_id: Optional[int] = None
    manufacturer_id: Optional[int] = Field(
        default=None, allow_none=True
    )  # Pozwól na ustawienie na None lub zmianę


class SensorTypeResponse(SensorTypeBase):
    id: int
    # Zagnieżdżone odpowiedzi dla powiązanych obiektów
    sensor_class: SensorClassResponse
    manufacturer: Optional[ManufacturerResponse] = None  # Producent może być opcjonalny
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
