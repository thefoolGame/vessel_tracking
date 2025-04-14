from pydantic import BaseModel
from datetime import datetime

class SensorClassBase(BaseModel):
    name: str
    description: str | None = None

class SensorClassCreate(SensorClassBase):
    pass

class SensorClassResponse(SensorClassBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
