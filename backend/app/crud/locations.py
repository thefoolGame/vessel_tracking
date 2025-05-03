from sqlalchemy.orm import Session
from app.models.models import Location
from app.schemas.location import LocationCreate
from geoalchemy2 import WKTElement
from geoalchemy2.shape import to_shape

def create_location(db: Session, location: LocationCreate):
    db_location = Location(
        vessel_id=location.vessel_id,
        position=WKTElement(location.position, srid=4326),
        accuracy_meters=location.accuracy_meters,
        source=location.source,
    )
    db.add(db_location)
    db.commit()
    db.refresh(db_location)

    # Explicitly serialize geometry here
    serialized_location = {
        "location_id": db_location.location_id,
        "vessel_id": db_location.vessel_id,
        "position": to_shape(db_location.position).wkt,
        "accuracy_meters": db_location.accuracy_meters,
        "source": db_location.source,
        "timestamp": db_location.timestamp,
    }

    return serialized_location

def get_location(db: Session, location_id: int):
    db_location = db.query(Location).get(location_id)
    if not db_location:
        return None  # FastAPI will handle this as a 404 if you raise an HTTPException

    return {
        "location_id": db_location.location_id,
        "vessel_id": db_location.vessel_id,
        "position": to_shape(db_location.position).wkt if db_location.position else None,
        "accuracy_meters": float(db_location.accuracy_meters),
        "source": db_location.source,
        "timestamp": db_location.timestamp,
    }

def get_locations(db: Session, skip: int = 0, limit: int = 100):
    db_locations = db.query(Location).offset(skip).limit(limit).all()

    result = []
    for loc in db_locations:
        result.append({
            "location_id": loc.location_id,
            "vessel_id": loc.vessel_id,
            "position": to_shape(loc.position).wkt if loc.position else None,
            "accuracy_meters": float(loc.accuracy_meters),  # just to be safe
            "source": loc.source,
            "timestamp": loc.timestamp,
        })

    return result
