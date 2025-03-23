from sqlalchemy import (
    CheckConstraint,
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    DateTime,
    Text,
    Boolean,
    Numeric,
    Date,
    JSON,
    event,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy.orm.session import object_session
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
import datetime

Base = declarative_base()

# Encje podstawowe


class Manufacturer(Base):
    """Producenci łodzi i czujników"""

    __tablename__ = "manufacturers"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    country = Column(String(50))
    contact_info = Column(JSON)
    website = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    vessel_types = relationship("VesselType", back_populates="manufacturer")
    # sensors = relationship("Sensor", back_populates="manufacturer")
    # sensor_types = relationship("SensorType", back_populates="manufacturer")


class Operator(Base):
    """Operatorzy zarządzający flotami łodzi"""

    __tablename__ = "operators"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    contact_person = Column(String(100))
    email = Column(String(100))
    phone = Column(String(20))
    address = Column(Text)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    fleets = relationship("Fleet", back_populates="operator")
    vessels = relationship("Vessel", back_populates="operator")


class Fleet(Base):
    """Floty pod wspólnym zarządem"""

    __tablename__ = "fleets"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    operator_id = Column(Integer, ForeignKey("operators.id", ondelete="RESTRICT"))
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    operator = relationship("Operator", back_populates="fleets")
    vessels = relationship("Vessel", back_populates="fleet")


class VesselType(Base):
    """Typy łodzi"""

    __tablename__ = "vessel_types"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    manufacturer_id = Column(
        Integer, ForeignKey("manufacturers.id", ondelete="RESTRICT")
    )
    length_meters = Column(Numeric(5, 2))
    width_meters = Column(Numeric(5, 2))
    draft_meters = Column(Numeric(4, 2))
    max_speed_knots = Column(Numeric(5, 2))
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    manufacturer = relationship("Manufacturer", back_populates="vessel_types")
    vessels = relationship("Vessel", back_populates="vessel_type")


class Vessel(Base):
    """Łodzie - główne jednostki floty"""

    __tablename__ = "vessels"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    vessel_type_id = Column(
        Integer, ForeignKey("vessel_types.id", ondelete="RESTRICT"), nullable=False
    )
    fleet_id = Column(
        Integer, ForeignKey("fleets.id", ondelete="RESTRICT"), nullable=True
    )
    operator_id = Column(
        Integer, ForeignKey("operators.id", ondelete="RESTRICT"), nullable=False
    )
    production_year = Column(Integer)
    registration_number = Column(String(50), unique=True)
    imo_number = Column(String(20), unique=True)
    mmsi_number = Column(String(20), unique=True)
    call_sign = Column(String(20), unique=True)
    status = Column(
        String(20),
        CheckConstraint(
            "status IN ('active', 'maintenance', 'retired', 'out_of_service')"
        ),
        default="active",
    )
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    vessel_type = relationship("VesselType", back_populates="vessels")
    fleet = relationship("Fleet", back_populates="vessels")
    operator = relationship("Operator", back_populates="vessels")

    @property
    def manufacturer(self):
        """Zwraca producenta łodzi na podstawie producenta typu łodzi"""
        return self.vessel_type.manufacturer if self.vessel_type else None

    @validates("fleet_id")
    def validate_fleet(self, key, fleet_id):
        """Walidacja zapewniająca, że po przypisaniu floty operator jest zgodny z operatorem floty"""
        if fleet_id is not None:
            session = object_session(self)
            if session:
                fleet = session.query(Fleet).get(fleet_id)
                if fleet:
                    # Automatycznie aktualizujemy operator_id, aby był zgodny z flotą
                    self.operator_id = fleet.operator_id
            else:
                # Gdy obiekt nie jest jeszcze w sesji (nowy obiekt)
                # Zachowaj wartość fleet_id, walidacja zostanie wykonana przed zapisem
                pass
        return fleet_id

    @validates("operator_id")
    def validate_operator(self, key, operator_id):
        """Walidacja zapewniająca, że operator jest zgodny z operatorem floty (jeśli przypisana)"""
        if self.fleet_id is not None:
            session = object_session(self)
            if session:
                fleet = session.query(Fleet).get(self.fleet_id)
                if fleet and operator_id != fleet.operator_id:
                    raise ValueError(
                        "Operator must match the fleet's operator when vessel is assigned to a fleet"
                    )
        return operator_id


@event.listens_for(Vessel, "before_insert")
@event.listens_for(Vessel, "before_update")
def check_vessel_fleet_operator_consistency(mapper, connection, vessel):
    if vessel.fleet_id is not None:
        # Pobierz sesję
        session = object_session(vessel)
        if session:
            # Pobierz flotę
            fleet = session.query(Fleet).get(vessel.fleet_id)
            if fleet and vessel.operator_id != fleet.operator_id:
                raise ValueError(
                    "Operator must match the fleet's operator when vessel is assigned to a fleet"
                )
