from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import SessionLocal
from app.schemas.public_map import PublicVesselMapData
from app.crud import (
    public_map as crud_public_map,
)

router = APIRouter(prefix="/alerts", tags=["alerts"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


router = APIRouter(
    prefix="/public",
    tags=["Public Data"],
)


@router.get(
    "/map/initial-vessels",
    response_model=List[PublicVesselMapData],
    summary="Get initial data for public map display (vessels, latest positions, planned routes)",
    # Ten endpoint NIE MA autoryzacji
)
def get_public_map_data(db: Session = Depends(get_db)):
    data = crud_public_map.get_public_map_initial_data(db=db)
    return data
