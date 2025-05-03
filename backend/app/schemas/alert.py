from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AlertBase(BaseModel):
    vessel_id: int
    sensor_id: Optional[int]
    alert_type: str
    severity: str
    message: str
    acknowledged: Optional[bool] = False
    acknowledged_by: Optional[int]
    acknowledged_at: Optional[datetime]
    resolved: Optional[bool] = False
    resolved_at: Optional[datetime]
    notes: Optional[str]

class AlertCreate(AlertBase):
    pass

class AlertResponse(AlertBase):
    alert_id: int
    timestamp: datetime

    class Config:
        orm_mode = True

