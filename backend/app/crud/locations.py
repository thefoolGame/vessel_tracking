from sqlalchemy.orm import Session, aliased
from sqlalchemy import func, desc, select, literal_column
from app.models.models import Location, Vessel
from app.schemas.location import LocationCreate
from app.schemas.vessel import VesselLatestLocationResponse
from geoalchemy2 import WKTElement
from geoalchemy2.shape import to_shape
from typing import List, Dict, Any, Optional


def create_location(db: Session, location: LocationCreate) -> Location:
    vessel = db.query(Vessel).get(location.vessel_id)
    if not vessel:
        raise ValueError(f"Vessel with id {location.vessel_id} not found.")

    db_location = Location(
        vessel_id=location.vessel_id,
        position=WKTElement(location.position, srid=4326),
        heading=location.heading,
        accuracy_meters=location.accuracy_meters,
        source=location.source,
    )
    try:
        db.add(db_location)
        db.commit()
        db.refresh(db_location)
    except Exception:
        db.rollback()
        raise
    return db


def get_location_by_id(db: Session, location_id: int) -> Optional[Location]:
    return db.query(Location).get(location_id)


def get_all_locations(db: Session, skip: int = 0, limit: int = 1000) -> List[Location]:
    return (
        db.query(Location)
        .order_by(desc(Location.timestamp))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_locations_by_vessel_id(
    db: Session, vessel_id: int, limit: int = 1000
) -> List[Location]:
    return (
        db.query(Location)
        .filter(Location.vessel_id == vessel_id)
        .order_by(desc(Location.timestamp))
        .limit(limit)
        .all()
    )


def get_latest_location_for_each_vessel(
    db: Session,
) -> List[VesselLatestLocationResponse]:
    """
    Pobiera najnowszą lokalizację dla każdego statku, który ma jakiekolwiek lokalizacje,
    wraz z przedostatnią lokalizacją do obliczenia kierunku.
    """
    # Podzapytanie do znalezienia najnowszego timestampu dla każdego statku
    latest_ts_sq = (
        db.query(
            Location.vessel_id,
            func.max(Location.timestamp).label("max_timestamp"),
        )
        .group_by(Location.vessel_id)
        .subquery("latest_ts_sq")
    )

    # Aliasy dla tabel Location i Vessel
    l1 = aliased(Location, name="l1")
    v = aliased(Vessel, name="v")

    query_results = (
        db.query(
            l1.vessel_id,
            v.name.label("vessel_name"),
            l1.position.label("latest_position"),
            l1.heading.label("latest_heading"),
            l1.timestamp.label("latest_timestamp"),
        )
        .join(
            latest_ts_sq,
            (l1.vessel_id == latest_ts_sq.c.vessel_id)
            & (l1.timestamp == latest_ts_sq.c.max_timestamp),
        )
        .join(v, v.id == l1.vessel_id)
        .all()
    )

    response_data: List[VesselLatestLocationResponse] = []
    for row in query_results:
        response_data.append(
            VesselLatestLocationResponse(
                vessel_id=row.vessel_id,
                name=row.vessel_name,
                latest_position_wkt=to_shape(row.latest_position).wkt
                if row.latest_position
                else None,
                latest_timestamp=row.latest_timestamp,
                latest_heading=row.latest_heading,
            )
        )
    return response_data


def get_latest_location_for_vessel(db: Session, vessel_id: int) -> Optional[Location]:
    return (
        db.query(Location)
        .filter(Location.vessel_id == vessel_id)
        .order_by(Location.timestamp.desc())
        .first()
    )
