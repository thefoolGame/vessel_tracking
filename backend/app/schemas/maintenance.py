from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MaintenanceBase(BaseModel):
    vessel_id: int
    maintenance_type: str
    description: Optional[str]
    start_date: datetime
    end_date: Optional[datetime]
    status: Optional[str] = "planned"
    performed_by: Optional[str]
    cost: Optional[float]
    notes: Optional[str]

class MaintenanceCreate(MaintenanceBase):
    pass

class MaintenanceResponse(MaintenanceBase):
    maintenance_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
