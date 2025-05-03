from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import SessionLocal
from app.schemas.vessel_parameter import VesselParameterCreate, VesselParameterResponse
from app.crud import vessel_parameter as crud_param

router = APIRouter(prefix="/vessel-parameters", tags=["vessel_parameters"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=VesselParameterResponse)
def create_parameter(param: VesselParameterCreate, db: Session = Depends(get_db)):
    return crud_param.create_vessel_parameter(db=db, param=param)

@router.get("/{parameter_id}", response_model=VesselParameterResponse)
def read_parameter(parameter_id: int, db: Session = Depends(get_db)):
    db_param = crud_param.get_vessel_parameter(db, parameter_id)
    if db_param is None:
        raise HTTPException(status_code=404, detail="Parameter not found")
    return db_param

@router.get("/", response_model=List[VesselParameterResponse])
def read_parameters(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_param.get_vessel_parameters(db=db, skip=skip, limit=limit)
