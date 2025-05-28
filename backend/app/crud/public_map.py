from sqlalchemy.orm import Session
from typing import List
from app.models.models import Vessel, Location, RoutePoint
from app.schemas.public_map import PublicVesselMapData
from app.schemas.route_point import RoutePointResponse  # Potrzebne do konwersji
from geoalchemy2.shape import to_shape
from sqlalchemy import desc


def get_public_map_initial_data(db: Session) -> List[PublicVesselMapData]:
    results = []
    vessels = (
        db.query(Vessel).filter(Vessel.status == "active").all()
    )  # Tylko aktywne statki

    for vessel in vessels:
        latest_location = (
            db.query(Location)
            .filter(Location.vessel_id == vessel.id)
            .order_by(desc(Location.timestamp))
            .first()
        )

        planned_route_db = (
            db.query(RoutePoint)
            .filter(RoutePoint.vessel_id == vessel.id)
            .filter(RoutePoint.status == "planned")
            .order_by(RoutePoint.sequence_number)
            .all()
        )

        planned_route_pydantic: List[RoutePointResponse] = []
        for rp_db in planned_route_db:
            planned_route_pydantic.append(RoutePointResponse.model_validate(rp_db))

        vessel_map_data = PublicVesselMapData(
            vessel_id=vessel.id,
            name=vessel.name,
            latest_position_wkt=to_shape(latest_location.position).wkt
            if latest_location and latest_location.position
            else None,
            latest_heading=latest_location.heading if latest_location else None,
            latest_timestamp=latest_location.timestamp if latest_location else None,
            planned_route=planned_route_pydantic,
        )
        results.append(vessel_map_data)
    return results
