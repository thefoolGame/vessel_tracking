from fastapi import FastAPI
from app.models.models import Base
from app.core.database import engine
from app.routes import operators, vessel_types, fleets, vessels, manufacturers

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Vessel Tracking API")

app.include_router(vessels.router)
app.include_router(operators.router)
app.include_router(vessel_types.router)
app.include_router(fleets.router)
app.include_router(vessels.router)
app.include_router(manufacturers.router)
@app.get("/")
def root():
    return {"message": "Backend działa poprawnie"}
