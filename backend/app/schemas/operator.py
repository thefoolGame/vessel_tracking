from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class OperatorBase(BaseModel):
    name: str
    contact_person: Optional[str] = None
    email: Optional[EmailStr] = None  # Użycie EmailStr dla walidacji
    phone: Optional[str] = None
    address: Optional[str] = None


class OperatorCreate(OperatorBase):
    pass


class OperatorUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class OperatorResponse(OperatorBase):
    id: int
    created_at: datetime
    updated_at: datetime
    fleets_count: int = 0
    vessels_count: int = 0

    class Config:
        from_attributes = True
