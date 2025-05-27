from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Dict
from app.models.models import (
    Vessel,
    VesselType,
    Fleet,
    Operator,
    SensorClass,
    vessel_type_required_sensor_types,
)
from app.schemas.vessel import (
    VesselCreate,
    VesselUpdate,
    AllowedSensorClassDetail,
    VesselSensorConfigurationStatusResponse,
)


def get_vessel(db: Session, vessel_id: int) -> Optional[Vessel]:
    return db.query(Vessel).filter(Vessel.id == vessel_id).first()


def get_vessels(db: Session, skip: int = 0, limit: int = 100) -> List[Vessel]:
    return db.query(Vessel).order_by(Vessel.name).offset(skip).limit(limit).all()


def get_vessels_by_fleet(
    db: Session, fleet_id: int, skip: int = 0, limit: int = 100
) -> List[Vessel]:
    return (
        db.query(Vessel)
        .filter(Vessel.fleet_id == fleet_id)
        .order_by(Vessel.name)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_vessels_by_operator(
    db: Session, operator_id: int, skip: int = 0, limit: int = 100
) -> List[Vessel]:
    return (
        db.query(Vessel)
        .filter(Vessel.operator_id == operator_id)
        .order_by(Vessel.name)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_vessel(db: Session, vessel: VesselCreate) -> Vessel:
    # Walidacja istnienia FK przed próbą utworzenia
    if not db.query(VesselType).filter(VesselType.id == vessel.vessel_type_id).first():
        raise ValueError(f"VesselType with id {vessel.vessel_type_id} not found.")
    if not db.query(Operator).filter(Operator.id == vessel.operator_id).first():
        raise ValueError(f"Operator with id {vessel.operator_id} not found.")
    if (
        vessel.fleet_id
        and not db.query(Fleet).filter(Fleet.id == vessel.fleet_id).first()
    ):
        raise ValueError(f"Fleet with id {vessel.fleet_id} not found.")

    # Walidator SQLAlchemy @validates("fleet_id") w modelu Vessel
    # powinien automatycznie ustawić operator_id, jeśli fleet_id jest podane.
    # Jeśli fleet_id jest podane, a operator_id z VesselCreate nie pasuje do operatora floty,
    # walidator @validates("operator_id") powinien rzucić błąd.

    db_vessel = Vessel(**vessel.model_dump())
    try:
        db.add(db_vessel)
        db.commit()
        db.refresh(db_vessel)
        return db_vessel
    except IntegrityError as e:  # Np. unikalne pola jak registration_number
        db.rollback()
        # Sprawdź, czy błąd dotyczy konkretnego pola, np. unikalności
        # psycopg2.errors.UniqueViolation
        orig_error = getattr(e, "orig", None)
        if (
            orig_error
            and hasattr(orig_error, "diag")
            and hasattr(orig_error.diag, "constraint_name")
        ):
            constraint_name = orig_error.diag.constraint_name
            if "registration_number" in constraint_name:
                raise ValueError(
                    f"Vessel with registration number '{db_vessel.registration_number}' already exists."
                )
            elif "imo_number" in constraint_name:
                raise ValueError(
                    f"Vessel with IMO number '{db_vessel.imo_number}' already exists."
                )
            # Dodaj inne unikalne ograniczenia
        raise ValueError(
            f"Database integrity error: {str(e.orig)}"
        )  # Ogólny błąd integralności
    except ValueError as e:  # Przechwyć ValueError z walidatorów SQLAlchemy
        db.rollback()
        raise e  # Rzuć dalej
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"An unexpected error occurred: {str(e)}")


def update_vessel(
    db: Session, vessel_id: int, vessel_update: VesselUpdate
) -> Optional[Vessel]:
    db_vessel = get_vessel(db, vessel_id)
    if not db_vessel:
        return None

    update_data = vessel_update.model_dump(exclude_unset=True)

    # Walidacja FK przed aktualizacją
    if (
        "vessel_type_id" in update_data
        and not db.query(VesselType)
        .filter(VesselType.id == update_data["vessel_type_id"])
        .first()
    ):
        raise ValueError(
            f"VesselType with id {update_data['vessel_type_id']} not found."
        )
    if (
        "operator_id" in update_data
        and not db.query(Operator)
        .filter(Operator.id == update_data["operator_id"])
        .first()
    ):
        raise ValueError(f"Operator with id {update_data['operator_id']} not found.")
    if (
        "fleet_id" in update_data
        and update_data["fleet_id"] is not None
        and not db.query(Fleet).filter(Fleet.id == update_data["fleet_id"]).first()
    ):
        raise ValueError(f"Fleet with id {update_data['fleet_id']} not found.")

    # Logika dla fleet_id i operator_id, aby wyzwolić walidatory SQLAlchemy
    # Jeśli fleet_id jest zmieniane, pozwól walidatorowi @validates("fleet_id") zadziałać
    # Jeśli operator_id jest zmieniane, pozwól walidatorowi @validates("operator_id") zadziałać
    # SQLAlchemy powinno obsłużyć to automatycznie przy setattr

    for key, value in update_data.items():
        setattr(db_vessel, key, value)

    try:
        db.commit()
        db.refresh(db_vessel)
        return db_vessel
    except IntegrityError as e:
        db.rollback()
        # Podobna obsługa błędów unikalności jak w create_vessel
        orig_error = getattr(e, "orig", None)
        if (
            orig_error
            and hasattr(orig_error, "diag")
            and hasattr(orig_error.diag, "constraint_name")
        ):
            constraint_name = orig_error.diag.constraint_name
            # ... (obsługa konkretnych błędów unikalności) ...
        raise ValueError(f"Database integrity error during update: {str(e.orig)}")
    except ValueError as e:  # Przechwyć ValueError z walidatorów SQLAlchemy
        db.rollback()
        raise e
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"An unexpected error occurred during update: {str(e)}")


def delete_vessel(db: Session, vessel_id: int) -> Optional[Vessel]:
    db_vessel = get_vessel(db, vessel_id)
    if db_vessel:
        # Uwaga na ondelete="CASCADE" dla sensors, locations, ais_data, route_points, etc.
        # Jeśli są RESTRICT, usuwanie może się nie udać.
        try:
            db.delete(db_vessel)
            db.commit()
            return db_vessel
        except IntegrityError as e:
            db.rollback()
            raise ValueError(
                f"Cannot delete vessel. It might be associated with other records (e.g., locations, sensors). Details: {str(e.orig)}"
            )
    return None


def get_vessel_sensor_configuration_status(
    db: Session, vessel_id: int
) -> Optional[VesselSensorConfigurationStatusResponse]:
    db_vessel = db.query(Vessel).filter(Vessel.id == vessel_id).first()
    if not db_vessel:
        return None

    if not db_vessel.vessel_type:
        return VesselSensorConfigurationStatusResponse(
            vessel_id=db_vessel.id,
            vessel_name=db_vessel.name,
            vessel_type_id=0,
            vessel_type_name="N/A (Brak typu statku)",
            all_requirements_met=True,  # Brak typu = brak wymagań
            allowed_classes=[],
        )

    # 1. Pobierz WSZYSTKIE dozwolone (wymagane i opcjonalne) klasy czujników dla typu statku
    allowed_sensor_classes_query = (
        db.query(
            vessel_type_required_sensor_types.c.sensor_class_id,
            SensorClass.name.label("sensor_class_name"),
            vessel_type_required_sensor_types.c.quantity.label("defined_quantity"),
            vessel_type_required_sensor_types.c.required.label("is_required"),
        )
        .join(
            SensorClass,
            vessel_type_required_sensor_types.c.sensor_class_id == SensorClass.id,
        )
        .filter(
            vessel_type_required_sensor_types.c.vessel_type_id
            == db_vessel.vessel_type_id
        )
        .all()
    )

    # 2. Pobierz zainstalowane czujniki i pogrupuj po sensor_class_id
    installed_sensors_by_class: Dict[int, int] = {}
    for sensor_instance in db_vessel.sensors:  # Zmieniono nazwę zmiennej iteracyjnej
        if sensor_instance.sensor_type and sensor_instance.sensor_type.sensor_class_id:
            class_id = sensor_instance.sensor_type.sensor_class_id
            installed_sensors_by_class[class_id] = (
                installed_sensors_by_class.get(class_id, 0) + 1
            )

    # 3. Przygotuj listę dozwolonych klas i sprawdź status
    allowed_classes_details_list: List[AllowedSensorClassDetail] = []
    all_requirements_met_flag = True

    for allowed_class_info in allowed_sensor_classes_query:
        installed_qty = installed_sensors_by_class.get(
            allowed_class_info.sensor_class_id, 0
        )
        is_met_for_class = None
        if allowed_class_info.is_required:
            is_met_for_class = installed_qty >= allowed_class_info.defined_quantity
            if not is_met_for_class:
                all_requirements_met_flag = False

        allowed_classes_details_list.append(
            AllowedSensorClassDetail(
                sensor_class_id=allowed_class_info.sensor_class_id,
                sensor_class_name=allowed_class_info.sensor_class_name,
                is_required=allowed_class_info.is_required,
                defined_quantity=allowed_class_info.defined_quantity,
                installed_quantity=installed_qty,
                is_requirement_met=is_met_for_class,
            )
        )

    allowed_classes_details_list.sort(
        key=lambda x: (-x.is_required, x.sensor_class_name)
    )

    return VesselSensorConfigurationStatusResponse(
        vessel_id=db_vessel.id,
        vessel_name=db_vessel.name,
        vessel_type_id=db_vessel.vessel_type_id,
        vessel_type_name=db_vessel.vessel_type.name,
        all_requirements_met=all_requirements_met_flag,
        allowed_classes=allowed_classes_details_list,
    )
