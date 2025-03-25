from sqlalchemy import (
    Table,
    CheckConstraint,
    Column,
    BigInteger,
    Integer,
    String,
    Float,
    ForeignKey,
    DateTime,
    Text,
    Boolean,
    Numeric,
    Index,
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

vessel_type_required_sensor_types = Table(
    "vessel_type_required_sensor_types",
    Base.metadata,
    Column(
        "vessel_type_id",
        Integer,
        ForeignKey("vessel_types.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "sensor_class_id",
        Integer,
        ForeignKey("sensor_classes.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "required", Boolean, default=True, nullable=False
    ),  # Określa czy czujnik jest wymagany czy opcjonalny
    Column(
        "quantity", Integer, default=1, nullable=False
    ),  # Określa ilość czujników danego typu
    Column("created_at", DateTime(timezone=True), default=func.now()),
)

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
    sensor_types = relationship("SensorType", back_populates="manufacturer")


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
    required_sensor_classes = relationship(
        "SensorClass",
        secondary=vessel_type_required_sensor_types,
        backref="used_in_vessel_types",
    )


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
    sensors = relationship("Sensor", back_populates="vessel")

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

    def validate_sensors(self):
        """
        Sprawdza czy łódź ma zainstalowane wszystkie wymagane czujniki
        zgodnie z definicją typu łodzi
        """
        # Pobierz wszystkie wymagane klasy czujników dla typu łodzi
        required_classes = {}

        for link in (
            object_session(self)
            .query(vessel_type_required_sensor_types)
            .filter_by(vessel_type_id=self.vessel_type_id, required=True)
            .all()
        ):
            required_classes[link.sensor_class_id] = link.quantity

        # Pobierz wszystkie zainstalowane czujniki pogrupowane według klas
        installed_sensors = {}
        for sensor in self.sensors:
            class_id = sensor.sensor_type.sensor_class_id
            if class_id in installed_sensors:
                installed_sensors[class_id] += 1
            else:
                installed_sensors[class_id] = 1

        # Sprawdź czy wszystkie wymagane klasy są pokryte
        missing_sensors = {}
        for class_id, required_qty in required_classes.items():
            installed_qty = installed_sensors.get(class_id, 0)
            if installed_qty < required_qty:
                missing_sensors[class_id] = required_qty - installed_qty

        return missing_sensors


class SensorClass(Base):
    """Klasy czujników (np. GPS, IMU)"""

    __tablename__ = "sensor_classes"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    sensor_types = relationship("SensorType", back_populates="sensor_class")

    def __repr__(self):
        return f"<SensorClass(name='{self.name}')>"


class SensorType(Base):
    """
    Konkretna implementacja czujnika od danego producenta
    należąca do określonej kategorii czujników
    """

    __tablename__ = "sensor_types"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    sensor_class_id = Column(
        Integer, ForeignKey("sensor_classes.id", ondelete="RESTRICT"), nullable=False
    )
    manufacturer_id = Column(
        Integer,
        ForeignKey("manufacturers.id", ondelete="RESTRICT"),
    )
    measurement_unit = Column(String(50))
    min_val = Column(Numeric)
    max_val = Column(Numeric)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    manufacturer = relationship("Manufacturer", back_populates="sensor_types")
    sensor_class = relationship("SensorClass", back_populates="sensor_types")
    sensors = relationship("Sensor", back_populates="sensor_type")


class Sensor(Base):
    """Konkretny czujnik zainstalowany na łodzi"""

    __tablename__ = "sensors"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    sensor_type_id = Column(
        Integer, ForeignKey("sensor_types.id", ondelete="RESTRICT"), nullable=False
    )
    vessel_id = Column(
        Integer, ForeignKey("vessels.id", ondelete="CASCADE"), nullable=False
    )
    serial_number = Column(String(100))
    installation_date = Column(Date)
    callibration_date = Column(Date)
    location_on_boat = Column(Text)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    sensor_type = relationship("SensorType", back_populates="sensors")
    readings = relationship("SensorReading", back_populates="sensor")
    vessel = relationship("Vessel", back_populates="sensors")

    @validates("sensor_type_id")
    def validate_sensor_type(self, key, sensor_type_id):
        """
        Waliduje, że wybrany typ czujnika jest zgodny z wymaganiami typu łodzi.
        Sprawdza, czy kategoria czujnika jest wymagana lub dozwolona dla typu łodzi.
        """
        session = object_session(self)

        # Jeśli sesja nie istnieje (np. nowy obiekt) lub nie ma vessel_id,
        # odłóż walidację do później
        if not session or not self.vessel_id:
            return sensor_type_id

        # Pobierz typ łodzi i kategorię czujnika
        vessel = session.query(Vessel).get(self.vessel_id)
        sensor_type = session.query(SensorType).get(sensor_type_id)

        if not vessel or not sensor_type:
            return sensor_type_id

        # Sprawdź czy klasa czujnika jest dozwolona dla tego typu łodzi
        allowed_classes = (
            session.query(vessel_type_required_sensor_types)
            .filter_by(vessel_type_id=vessel.vessel_type_id)
            .all()
        )

        allowed_class_ids = [link.sensor_class_id for link in allowed_classes]

        if sensor_type.sensor_class_id not in allowed_class_ids:
            raise ValueError(
                f"Sensor type of class '{sensor_type.sensor_class.name}' is not allowed for vessel type '{vessel.vessel_type.name}'"
            )

        return sensor_type_id


# Encje operacyjne


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(BigInteger, primary_key=True)
    sensor_id = Column(
        Integer, ForeignKey("sensors.id", ondelete="CASCADE"), nullable=False
    )
    value = Column(Numeric, nullable=False)
    status = Column(
        String(20),
        CheckConstraint("status IN ('normal', 'warning', 'critical', 'error')"),
        default="normal",
    )
    timestamp = Column(DateTime(timezone=True), default=func.now())

    sensor = relationship("Sensor", back_populates="readings")

    __table_args__ = (
        Index("idx_sensor_readings_timestamp", timestamp),
        Index("idx_sensor_readings_sensor_timestamp", sensor_id, timestamp),
    )


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
