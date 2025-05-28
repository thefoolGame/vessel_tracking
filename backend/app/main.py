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
    ais_data,
    locations,
    route_points,
    sensor_readings,
    alert,
    maintenance,
    vessel_parameter,
    weather,
    public,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Vessel Tracking API")

app.include_router(operators.router)
app.include_router(vessel_types.router)
app.include_router(fleets.router)
app.include_router(vessels.router)
app.include_router(vessel_parameter.router)
app.include_router(maintenance.router)
app.include_router(manufacturers.router)
app.include_router(sensor_classes.router)
app.include_router(sensor_types.router)
app.include_router(sensors.router)
app.include_router(sensor_readings.router)
app.include_router(ais_data.router)
app.include_router(locations.router)
app.include_router(route_points.router)
app.include_router(alert.router)
app.include_router(weather.router)
app.include_router(public.router)


@app.get("/")
def root():
    return {"message": "Backend działa poprawnie"}

