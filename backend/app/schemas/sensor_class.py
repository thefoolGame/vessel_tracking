from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SensorClassBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class SensorClassCreate(SensorClassBase):
    pass


class SensorClassUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None


class SensorClassResponse(SensorClassBase):
    id: int

    class Config:
        from_attributes = True
