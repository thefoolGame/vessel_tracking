from fastapi import FastAPI
from app.models.models import Base
from app.core.database import engine

# Import routerów
from app.routes import (
    operators,
    vessel_types,
    fleets,
    vessels,
    manufacturers,
    sensor_classes,
    sensor_types,
    sensors,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Vessel Tracking API")

app.include_router(operators.router)
app.include_router(vessel_types.router)
app.include_router(fleets.router)
app.include_router(vessels.router)
app.include_router(manufacturers.router)
app.include_router(sensor_classes.router)
app.include_router(sensor_types.router)
app.include_router(sensors.router)
@app.get("/")
def root():
    return {"message": "Backend działa poprawnie"}
