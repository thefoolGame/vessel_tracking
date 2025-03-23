from sqlalchemy import (
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
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
import datetime

Base = declarative_base()
schema = "vessel_tracking"

# Encje podstawowe


class Manufacturer(Base):
    __tablename__ = "manufacturers"
    __table_args__ = {"schema": schema}

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    country = Column(String(50))
    contact_info = Column(Text)
    website = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    # Relacje
    # vessels = relationship("Vessel", back_populates="manufacturer")
    # sensors = relationship("Sensor", back_populates="manufacturer")
