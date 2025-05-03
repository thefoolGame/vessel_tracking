from sqlalchemy.orm import Session
from app.models.models import AisData
from app.schemas.ais_data import AisDataCreate
from geoalchemy2 import WKTElement
from geoalchemy2.shape import to_shape

def create_ais_data(db: Session, ais_data: AisDataCreate):
    db_ais_data = AisData(
        vessel_id=ais_data.vessel_id,
        position=WKTElement(ais_data.position, srid=4326),
        course_over_ground=ais_data.course_over_ground,
        speed_over_ground=ais_data.speed_over_ground,
        rate_of_turn=ais_data.rate_of_turn,
        navigation_status=ais_data.navigation_status,
        raw_data=ais_data.raw_data,
    )
    db.add(db_ais_data)
    db.commit()
    db.refresh(db_ais_data)

    return {
        "ais_data_id": db_ais_data.ais_data_id,
        "vessel_id": db_ais_data.vessel_id,
        "position": to_shape(db_ais_data.position).wkt,
        "course_over_ground": float(db_ais_data.course_over_ground),
        "speed_over_ground": float(db_ais_data.speed_over_ground),
        "rate_of_turn": float(db_ais_data.rate_of_turn),
        "navigation_status": db_ais_data.navigation_status,
        "raw_data": db_ais_data.raw_data,
        "timestamp": db_ais_data.timestamp,
    }

def get_ais_data(db: Session, ais_data_id: int):
    db_data = db.query(AisData).get(ais_data_id)
    if not db_data:
        return None
    return {
        "ais_data_id": db_data.ais_data_id,
        "vessel_id": db_data.vessel_id,
        "position": to_shape(db_data.position).wkt,
        "course_over_ground": float(db_data.course_over_ground),
        "speed_over_ground": float(db_data.speed_over_ground),
        "rate_of_turn": float(db_data.rate_of_turn),
        "navigation_status": db_data.navigation_status,
        "raw_data": db_data.raw_data,
        "timestamp": db_data.timestamp,
    }

def get_ais_datas(db: Session, skip: int = 0, limit: int = 100):
    results = db.query(AisData).offset(skip).limit(limit).all()
    return [
        {
            "ais_data_id": data.ais_data_id,
            "vessel_id": data.vessel_id,
            "position": to_shape(data.position).wkt,
            "course_over_ground": float(data.course_over_ground),
            "speed_over_ground": float(data.speed_over_ground),
            "rate_of_turn": float(data.rate_of_turn),
            "navigation_status": data.navigation_status,
            "raw_data": data.raw_data,
            "timestamp": data.timestamp,
        }
        for data in results
    ]
