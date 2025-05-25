from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from .operator import OperatorResponse


class FleetBase(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    operator_id: int  # Klucz obcy do Operatora


class FleetCreate(FleetBase):
    pass


class FleetUpdate(BaseModel):  # Osobna klasa dla aktualizacji, aby pola były opcjonalne
    name: Optional[str] = Field(default=None, min_length=1)
    description: Optional[str] = None
    operator_id: Optional[int] = None  # Operator może być zmieniany


class FleetResponse(FleetBase):
    id: int
    created_at: datetime
    updated_at: datetime
    operator: Optional[OperatorResponse] = None  # Zagnieżdżony obiekt Operatora
    vessel_count: int = 0

    class Config:
        from_attributes = True
