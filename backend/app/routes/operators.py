from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.schemas.operator import OperatorCreate, OperatorResponse
from app.crud import operators as crud_operators
from typing import List

router = APIRouter(prefix="/operators", tags=["operators"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=OperatorResponse)
def create_operator(operator: OperatorCreate, db: Session = Depends(get_db)):
    return crud_operators.create_operator(db=db, operator=operator)

@router.get("/{operator_id}", response_model=OperatorResponse)
def read_operator(operator_id: int, db: Session = Depends(get_db)):
    db_operator = crud_operators.get_operator(db, operator_id=operator_id)
    if db_operator is None:
        raise HTTPException(status_code=404, detail="Operator not found")
    return db_operator


@router.get("/", response_model=List[OperatorResponse])
def read_operators(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_operators.get_operators(db=db, skip=skip, limit=limit)
