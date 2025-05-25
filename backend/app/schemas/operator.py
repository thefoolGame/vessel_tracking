from pydantic import BaseModel


class OperatorBase(BaseModel):
    name: str


class OperatorCreate(OperatorBase):
    pass


class OperatorResponse(OperatorBase):
    id: int

    class Config:
        from_attributes = True
