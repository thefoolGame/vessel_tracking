from sqlalchemy.orm import Session, joinedload, selectinload
from app.models.models import Vessel, Fleet, Operator, VesselType
from app.schemas.vessel import VesselCreate
from fastapi import HTTPException


def create_vessel(db: Session, vessel: VesselCreate):
    # sprawdzamy czy VesselType istnieje
    vessel_type = db.query(VesselType).get(vessel.vessel_type_id)
    if not vessel_type:
        raise HTTPException(status_code=400, detail="VesselType does not exist")

    # sprawdzamy czy Operator istnieje
    operator = db.query(Operator).get(vessel.operator_id)
    if not operator:
        raise HTTPException(status_code=400, detail="Operator does not exist")

    # jeśli fleet_id podano, sprawdzamy czy flota istnieje oraz czy operator floty zgadza się z operatorem podanym
    if vessel.fleet_id is not None:
        fleet = db.query(Fleet).get(vessel.fleet_id)
        if not fleet:
            raise HTTPException(status_code=400, detail="Fleet does not exist")
        if fleet.operator_id != vessel.operator_id:
            raise HTTPException(
                status_code=400, detail="Fleet operator and vessel operator mismatch"
            )

    db_vessel = Vessel(**vessel.dict())
    db.add(db_vessel)
    db.commit()
    db.refresh(db_vessel)
    return db_vessel


def get_vessel(db: Session, vessel_id: int):
    return (
        db.query(Vessel)
        .options(
            joinedload(Vessel.fleet),
            joinedload(Vessel.vessel_type),
            joinedload(Vessel.operator),
        )
        .filter(Vessel.id == vessel_id)
        .first()
    )


def get_vessels(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(Vessel)
        .options(
            selectinload(Vessel.fleet),
            selectinload(Vessel.vessel_type),
            selectinload(Vessel.operator),
        )
        .order_by(Vessel.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
