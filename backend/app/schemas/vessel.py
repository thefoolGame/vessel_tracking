# app/schemas/vessel.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal  # Jeśli jakieś pola Vessel lub zagnieżdżone tego wymagają

from .vessel_type import VesselTypeResponse
from .fleet import FleetResponse
from .operator import OperatorResponse


class VesselBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    vessel_type_id: int
    operator_id: int  # To pole będzie kluczowe dla walidacji z fleet_id
    fleet_id: Optional[int] = None
    production_year: Optional[int] = Field(
        default=None, ge=1800, le=datetime.now().year + 5
    )
    registration_number: Optional[str] = Field(default=None, max_length=50)
    imo_number: Optional[str] = Field(default=None, max_length=20)
    mmsi_number: Optional[str] = Field(default=None, max_length=20)
    call_sign: Optional[str] = Field(default=None, max_length=20)
    status: str = Field(
        default="active", pattern="^(active|maintenance|retired|out_of_service)$"
    )


class VesselCreate(VesselBase):
    # Walidator Pydantic, który może odzwierciedlać logikę z modelu SQLAlchemy
    # To jest walidacja na poziomie danych wejściowych API, zanim trafią do SQLAlchemy
    # Jednak główna walidacja spójności fleet/operator jest w modelu SQLAlchemy
    pass


class VesselUpdate(
    BaseModel
):  # Oddzielna klasa dla aktualizacji, wszystkie pola opcjonalne
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    vessel_type_id: Optional[int] = None
    operator_id: Optional[int] = None
    fleet_id: Optional[int] = (
        None  # Pozwalamy na ustawienie fleet_id na None (usunięcie z floty)
    )
    production_year: Optional[int] = Field(
        default=None, ge=1800, le=datetime.now().year + 5
    )
    registration_number: Optional[str] = Field(default=None, max_length=50)
    imo_number: Optional[str] = Field(default=None, max_length=20)
    mmsi_number: Optional[str] = Field(default=None, max_length=20)
    call_sign: Optional[str] = Field(default=None, max_length=20)
    status: Optional[str] = Field(
        default=None, pattern="^(active|maintenance|retired|out_of_service)$"
    )


class VesselResponse(VesselBase):  # Dziedziczy z VesselBase, więc ma te same pola
    id: int
    created_at: datetime
    updated_at: datetime

    # Zagnieżdżone odpowiedzi dla lepszego UX
    vessel_type: Optional[VesselTypeResponse] = None
    fleet: Optional[FleetResponse] = None
    operator: Optional[OperatorResponse] = None
    # sensors: List[SensorResponse] = [] # Można dodać później

    class Config:
        from_attributes = True


class VesselLatestLocationResponse(BaseModel):
    vessel_id: int
    name: str
    latest_position_wkt: Optional[str] = None
    latest_heading: Optional[Decimal] = None
    latest_timestamp: Optional[datetime] = None

    class Config:
        from_attributes = True


class AllowedSensorClassDetail(BaseModel):
    sensor_class_id: int
    sensor_class_name: str
    is_required: bool
    # Ilość zdefiniowana w tabeli vessel_type_required_sensor_types
    defined_quantity: int
    installed_quantity: int
    # Status 'is_met' ma sens głównie dla wymaganych klas.
    # Dla opcjonalnych, można by tu np. pokazać, czy limit został osiągnięty, jeśli 'defined_quantity' ma takie znaczenie.
    is_requirement_met: Optional[bool] = Field(
        default=None,
        description="True if sensor class is required and installed quantity meets defined quantity. Null otherwise.",
    )


class VesselSensorConfigurationStatusResponse(BaseModel):
    vessel_id: int
    vessel_name: str
    vessel_type_id: int
    vessel_type_name: str
    # Ogólny status spełnienia tylko dla *wymaganych* czujników
    all_requirements_met: bool = Field(
        description="True if all *required* sensor classes have their quantities met."
    )
    allowed_classes: List[AllowedSensorClassDetail] = Field(
        description="List of all sensor classes (required and optional) allowed for this vessel type, with their current installation status."
    )

    class Config:
        from_attributes = True
