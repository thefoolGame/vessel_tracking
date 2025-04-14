from pydantic import BaseModel

class VesselTypeBase(BaseModel):
    name: str
    manufacturer_id: int

class VesselTypeCreate(VesselTypeBase):
    pass

class VesselTypeResponse(VesselTypeBase):
    id: int

    class Config:
        orm_mode = True
