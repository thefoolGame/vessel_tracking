from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.schemas.route_point import RoutePointCreate, RoutePointResponse
from app.crud import route_points as crud
from typing import List

router = APIRouter(prefix="/route_points", tags=["route_points"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=RoutePointResponse)
def create_route_point(route_point: RoutePointCreate, db: Session = Depends(get_db)):
    return crud.create_route_point(db, route_point)

@router.get("/{route_point_id}", response_model=RoutePointResponse)
def read_route_point(route_point_id: int, db: Session = Depends(get_db)):
    route_point = crud.get_route_point(db, route_point_id)
    if route_point is None:
        raise HTTPException(status_code=404, detail="RoutePoint not found")
    return route_point

@router.get("/", response_model=List[RoutePointResponse])
def read_all_route_points(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_route_points(db, skip=skip, limit=limit)
