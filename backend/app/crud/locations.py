from sqlalchemy.orm import Session, aliased
from sqlalchemy import func, desc, select, literal_column
from app.models.models import Location, Vessel
from sqlalchemy.exc import IntegrityError
from app.schemas.location import LocationCreate, LocationUpdate
from app.schemas.vessel import VesselLatestLocationResponse
from geoalchemy2 import WKTElement
from geoalchemy2.shape import to_shape
from typing import List, Dict, Any, Optional
from datetime import datetime


def get_location_entry(
    db: Session, location_id: int, vessel_id: Optional[int] = None
) -> Optional[Location]:
    query = db.query(Location).filter(Location.location_id == location_id)
    if vessel_id is not None:
        query = query.filter(Location.vessel_id == vessel_id)
    return query.first()


def get_location_entries_for_vessel(
    db: Session,
    vessel_id: int,
    skip: int = 0,
    limit: int = 100,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> List[Location]:
    db_vessel = db.query(Vessel).filter(Vessel.id == vessel_id).first()
    if not db_vessel:
        return []  # Statek nie istnieje

    query = db.query(Location).filter(Location.vessel_id == vessel_id)

    if start_time:
        query = query.filter(Location.timestamp >= start_time)
    if end_time:
        query = query.filter(Location.timestamp <= end_time)

    return (
        query.order_by(Location.timestamp.desc())  # Najnowsze najpierw
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_latest_location_for_vessel(  # Funkcja pomocnicza, może być przydatna
    db: Session, vessel_id: int
) -> Optional[Location]:
    db_vessel = db.query(Vessel).filter(Vessel.id == vessel_id).first()
    if not db_vessel:
        return None
    return (
        db.query(Location)
        .filter(Location.vessel_id == vessel_id)
        .order_by(Location.timestamp.desc())
        .first()
    )


def create_location_entry(  # Nazwa zmieniona dla spójności
    db: Session, location_in: LocationCreate, vessel_id: int
) -> Location:
    db_vessel = db.query(Vessel).filter(Vessel.id == vessel_id).first()
    if not db_vessel:
        raise ValueError(f"Vessel with id {vessel_id} not found.")

    # Tworzymy słownik z danymi, nadpisując/ustawiając 'source'
    location_data = location_in.model_dump(
        exclude={"position"}
    )  # Wykluczamy string WKT na razie
    location_data["source"] = "manual"  # Zawsze ustawiamy source na manual

    db_location = Location(
        **location_data,
        vessel_id=vessel_id,
        position=location_in.position,  # GeoAlchemy2 powinno obsłużyć konwersję WKT
        # Alternatywnie: position=func.ST_GeomFromText(location_in.position, 4326)
    )

    try:
        db.add(db_location)
        db.commit()
        db.refresh(db_location)
        return db_location
    except IntegrityError as e:  # Np. naruszenie CheckConstraint
        db.rollback()
        orig_error = getattr(e, "orig", None)
        error_detail = str(orig_error) if orig_error else str(e)
        # Sprawdzenie konkretnych błędów, np. chk_location_heading_range
        if "chk_location_heading_range" in error_detail.lower():
            raise ValueError(
                f"Invalid heading value. Must be between 0 and 359.99. Detail: {error_detail}"
            )
        raise ValueError(f"Database integrity error: {error_detail}")
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"An unexpected error occurred: {str(e)}")


def update_location_entry(
    db: Session,
    location_id: int,
    location_in: LocationUpdate,
    vessel_id: int,
) -> Optional[Location]:
    db_location = get_location_entry(db, location_id=location_id, vessel_id=vessel_id)
    if not db_location:
        return None

    update_data = location_in.model_dump(exclude_unset=True)

    # Zawsze ustawiamy source na "manual" przy aktualizacji z tego miejsca
    update_data["source"] = "manual"

    # Obsługa aktualizacji pozycji WKT
    if "position" in update_data and update_data["position"]:
        # GeoAlchemy2 powinno obsłużyć przypisanie stringu WKT
        db_location.position = update_data.pop("position")

    for key, value in update_data.items():
        setattr(db_location, key, value)

    try:
        db.commit()
        db.refresh(db_location)
        return db_location
    except IntegrityError as e:
        db.rollback()
        orig_error = getattr(e, "orig", None)
        error_detail = str(orig_error) if orig_error else str(e)
        if "chk_location_heading_range" in error_detail.lower():
            raise ValueError(
                f"Invalid heading value. Must be between 0 and 359.99. Detail: {error_detail}"
            )
        raise ValueError(f"Database integrity error during update: {error_detail}")
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"An unexpected error occurred during update: {str(e)}")


def delete_location_entry(
    db: Session, location_id: int, vessel_id: int
) -> Optional[Location]:
    db_location = get_location_entry(db, location_id=location_id, vessel_id=vessel_id)
    if not db_location:
        return None

    try:
        # Sprawdzenie, czy Location nie jest powiązane z WeatherData, jeśli ondelete="RESTRICT"
        # Model WeatherData ma ForeignKey do locations.location_id (bez ondelete, więc domyślnie NO ACTION/RESTRICT)
        if db_location.weather_data:  # Zakładając, że relacja nazywa się 'weather_data'
            raise ValueError(
                f"Cannot delete location entry (ID: {location_id}) as it is referenced by weather data."
            )

        db.delete(db_location)
        db.commit()
        return db_location
    except ValueError:  # Przechwycenie naszego własnego błędu
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        orig_error = getattr(e, "orig", None)
        error_detail = str(orig_error) if orig_error else str(e)
        raise ValueError(
            f"Cannot delete location entry. Database integrity error: {error_detail}"
        )
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"An unexpected error occurred during deletion: {str(e)}")
