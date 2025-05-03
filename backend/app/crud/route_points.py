from sqlalchemy.orm import Session
from app.models.models import RoutePoint
from app.schemas.route_point import RoutePointCreate
from geoalchemy2 import WKTElement
from geoalchemy2.shape import to_shape

def create_route_point(db: Session, point: RoutePointCreate):
    db_point = RoutePoint(
        vessel_id=point.vessel_id,
        sequence_number=point.sequence_number,
        planned_position=WKTElement(point.planned_position, srid=4326),
        planned_arrival_time=point.planned_arrival_time,
        planned_departure_time=point.planned_departure_time,
        actual_arrival_time=point.actual_arrival_time,
        status=point.status,
    )
    db.add(db_point)
    db.commit()
    db.refresh(db_point)

    return {
        "route_point_id": db_point.route_point_id,
        "vessel_id": db_point.vessel_id,
        "sequence_number": db_point.sequence_number,
        "planned_position": to_shape(db_point.planned_position).wkt,
        "planned_arrival_time": db_point.planned_arrival_time,
        "planned_departure_time": db_point.planned_departure_time,
        "actual_arrival_time": db_point.actual_arrival_time,
        "status": db_point.status,
        "created_at": db_point.created_at,
        "updated_at": db_point.updated_at,
    }

def get_route_point(db: Session, point_id: int):
    db_point = db.query(RoutePoint).get(point_id)
    if not db_point:
        return None
    return {
        "route_point_id": db_point.route_point_id,
        "vessel_id": db_point.vessel_id,
        "sequence_number": db_point.sequence_number,
        "planned_position": to_shape(db_point.planned_position).wkt,
        "planned_arrival_time": db_point.planned_arrival_time,
        "planned_departure_time": db_point.planned_departure_time,
        "actual_arrival_time": db_point.actual_arrival_time,
        "status": db_point.status,
        "created_at": db_point.created_at,
        "updated_at": db_point.updated_at,
    }

def get_route_points(db: Session, skip: int = 0, limit: int = 100):
    db_points = db.query(RoutePoint).offset(skip).limit(limit).all()
    return [
        {
            "route_point_id": pt.route_point_id,
            "vessel_id": pt.vessel_id,
            "sequence_number": pt.sequence_number,
            "planned_position": to_shape(pt.planned_position).wkt,
            "planned_arrival_time": pt.planned_arrival_time,
            "planned_departure_time": pt.planned_departure_time,
            "actual_arrival_time": pt.actual_arrival_time,
            "status": pt.status,
            "created_at": pt.created_at,
            "updated_at": pt.updated_at,
        }
        for pt in db_points
    ]
