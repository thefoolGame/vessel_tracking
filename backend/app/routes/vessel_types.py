from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.schemas.vessel_type import VesselTypeCreate, VesselTypeResponse
from app.crud import vessel_types as crud_vessel_types
from typing import List

router = APIRouter(prefix="/vessel_types", tags=["vessel_types"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=VesselTypeResponse)
def create_vessel_type(vessel_type: VesselTypeCreate, db: Session = Depends(get_db)):
    return crud_vessel_types.create_vessel_type(db=db, vessel_type=vessel_type)

@router.get("/{vessel_type_id}", response_model=VesselTypeResponse)
def read_vessel_type(vessel_type_id: int, db: Session = Depends(get_db)):
    db_vessel_type = crud_vessel_types.get_vessel_type(db, vessel_type_id=vessel_type_id)
    if db_vessel_type is None:
        raise HTTPException(status_code=404, detail="VesselType not found")
    return db_vessel_type

@router.get("/", response_model=List[VesselTypeResponse])
def read_vessel_types(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_vessel_types.get_vessel_types(db=db, skip=skip, limit=limit)