from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.schemas.ais_data import AisDataCreate, AisDataResponse
from app.crud import ais_data as crud
from typing import List

router = APIRouter(prefix="/ais_data", tags=["ais_data"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=AisDataResponse)
def create_ais_data(data: AisDataCreate, db: Session = Depends(get_db)):
    return crud.create_ais_data(db, data)

@router.get("/{ais_data_id}", response_model=AisDataResponse)
def read_ais_data(ais_data_id: int, db: Session = Depends(get_db)):
    data = crud.get_ais_data(db, ais_data_id)
    if data is None:
        raise HTTPException(status_code=404, detail="AIS data not found")
    return data

@router.get("/", response_model=List[AisDataResponse])
def read_all_ais_data(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_ais_datas(db, skip=skip, limit=limit)
