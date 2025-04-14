from pydantic import BaseModel

class FleetBase(BaseModel):
    name: str
    operator_id: int

class FleetCreate(FleetBase):
    pass

class FleetResponse(FleetBase):
    id: int

    class Config:
        orm_mode = True
