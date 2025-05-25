from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.models import SensorClass  # Twój model SQLAlchemy
from app.schemas.sensor_class import SensorClassCreate, SensorClassUpdate


def get_sensor_class(db: Session, sensor_class_id: int) -> Optional[SensorClass]:
    return db.query(SensorClass).filter(SensorClass.id == sensor_class_id).first()


def get_sensor_class_by_name(db: Session, name: str) -> Optional[SensorClass]:
    return db.query(SensorClass).filter(SensorClass.name == name).first()


def get_sensor_classes(
    db: Session, skip: int = 0, limit: int = 1000
) -> List[SensorClass]:  # Zwiększono domyślny limit
    return (
        db.query(SensorClass).order_by(SensorClass.name).offset(skip).limit(limit).all()
    )


def create_sensor_class(db: Session, sensor_class: SensorClassCreate) -> SensorClass:
    # Sprawdź, czy klasa o tej nazwie już nie istnieje
    db_sensor_class_by_name = get_sensor_class_by_name(db, name=sensor_class.name)
    if db_sensor_class_by_name:
        raise ValueError(
            f"Sensor class with name '{sensor_class.name}' already exists."
        )

    db_sensor_class = SensorClass(**sensor_class.model_dump())
    db.add(db_sensor_class)
    db.commit()
    db.refresh(db_sensor_class)
    return db_sensor_class


def update_sensor_class(
    db: Session, sensor_class_id: int, sensor_class_update: SensorClassUpdate
) -> Optional[SensorClass]:
    db_sensor_class = get_sensor_class(db, sensor_class_id)
    if db_sensor_class:
        update_data = sensor_class_update.model_dump(exclude_unset=True)

        # Jeśli nazwa jest aktualizowana, sprawdź unikalność nowej nazwy
        if "name" in update_data and update_data["name"] != db_sensor_class.name:
            existing_with_new_name = get_sensor_class_by_name(
                db, name=update_data["name"]
            )
            if existing_with_new_name and existing_with_new_name.id != sensor_class_id:
                raise ValueError(
                    f"Sensor class with name '{update_data['name']}' already exists."
                )

        for key, value in update_data.items():
            setattr(db_sensor_class, key, value)
        db.commit()
        db.refresh(db_sensor_class)
    return db_sensor_class


def delete_sensor_class(db: Session, sensor_class_id: int) -> Optional[SensorClass]:
    db_sensor_class = get_sensor_class(db, sensor_class_id)
    if db_sensor_class:
        # UWAGA: Sprawdź zależności! SensorClass jest powiązany z:
        # - SensorType (ondelete="RESTRICT")
        # - vessel_type_required_sensor_types (ondelete="CASCADE")
        # Jeśli istnieją SensorType powiązane z tą klasą, usunięcie się nie powiedzie.
        # Musisz obsłużyć ten przypadek (np. sprawdzić i zwrócić błąd, lub zmienić ondelete).
        # Na razie zakładamy, że logika obsługi zależności jest w API lub chcemy, aby rzuciło błąd.
        try:
            db.delete(db_sensor_class)
            db.commit()
            return db_sensor_class
        except Exception as e:  # Np. IntegrityError
            db.rollback()
            print(f"Error deleting sensor class {sensor_class_id}: {e}")
            raise  # Rzuć dalej, aby API mogło obsłużyć
    return None
