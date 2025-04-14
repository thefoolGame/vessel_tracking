from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any
from datetime import datetime

class ManufacturerBase(BaseModel):
    name: str
    country: Optional[str] = None
    contact_info: Optional[Dict[str, Any]] = None
    website: Optional[HttpUrl] = None

class ManufacturerCreate(ManufacturerBase):
    pass

class ManufacturerResponse(ManufacturerBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
