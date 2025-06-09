from fastapi import APIRouter, Request, Depends, HTTPException, status, Query
from fastapi.responses import HTMLResponse, JSONResponse
import httpx
import os
from datetime import datetime
from typing import Optional

from pa_app.utils.utils import templates

VESSEL_API_BASE_URL = os.getenv("VESSEL_API_URL")

router = APIRouter(
    prefix="/sensors-overview",
    tags=["Public Sensors Overview"],
)


@router.get(
    "/",
    response_class=HTMLResponse,
    name="serve_sensors_overview_page",
)
async def serve_sensors_overview_page_main(
    request: Request, vessel_id: Optional[int] = None, sensor_id: Optional[int] = None
):
    return templates.TemplateResponse(
        "sensors_overview.html",
        {
            "request": request,
            "page_title": "Przegląd Odczytów Sensorów",
            "preselected_vessel_id": vessel_id,
            "preselected_sensor_id": sensor_id,
        },
    )


@router.get(
    "/vessel/{vessel_id_path:int}",
    response_class=HTMLResponse,
    name="serve_sensors_overview_for_vessel",
)
async def serve_sensors_overview_page_for_vessel(request: Request, vessel_id_path: int):
    return templates.TemplateResponse(
        "sensors_overview.html",
        {
            "request": request,
            "page_title": f"Odczyty Sensorów dla Statku ID: {vessel_id_path}",
            "preselected_vessel_id": vessel_id_path,
            "preselected_sensor_id": None,
        },
    )


@router.get(
    "/vessel/{vessel_id_path:int}/sensor/{sensor_id_path:int}",
    response_class=HTMLResponse,
    name="serve_sensors_overview_for_sensor",
)
async def serve_sensors_overview_page_for_sensor(
    request: Request, vessel_id_path: int, sensor_id_path: int
):
    return templates.TemplateResponse(
        "sensors_overview.html",
        {
            "request": request,
            "page_title": f"Odczyty dla Sensora ID: {sensor_id_path} (Statek ID: {vessel_id_path})",
            "preselected_vessel_id": vessel_id_path,
            "preselected_sensor_id": sensor_id_path,
        },
    )


@router.get(
    "/api/vessels",  # Ścieżka np. /sensors-overview/api/vessels
    response_class=JSONResponse,
    name="proxy_public_get_vessels_list_for_sensors_page",
    summary="Proxy to fetch a list of vessels for sensor overview page",
)
async def proxy_public_get_vessels_list():
    async with httpx.AsyncClient() as client:
        try:
            api_url = f"{VESSEL_API_BASE_URL}/vessels/?limit=1000&status=active"
            response = await client.get(api_url)
            response.raise_for_status()
            # Możesz chcieć przefiltrować odpowiedź, aby zwracać tylko potrzebne pola (id, name)
            # vessels_data = [{"id": v["id"], "name": v["name"]} for v in response.json()]
            # return JSONResponse(content=vessels_data, status_code=response.status_code)
            return JSONResponse(
                content=response.json(), status_code=response.status_code
            )
        except httpx.HTTPStatusError as e:
            return JSONResponse(
                content=e.response.json()
                if e.response.content
                and e.response.headers.get("content-type") == "application/json"
                else {"detail": e.response.text},
                status_code=e.response.status_code,
            )
        except Exception as e:
            return JSONResponse(
                content={"detail": f"Proxy error fetching vessels list: {str(e)}"},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@router.get(
    "/api/vessels/{vessel_id}/sensors",  # Ścieżka np. /sensors-overview/api/vessels/1/sensors
    response_class=JSONResponse,
    name="proxy_public_get_sensors_for_vessel",
    summary="Proxy to fetch sensors for a specific vessel",
)
async def proxy_public_get_sensors_for_vessel(vessel_id: int):
    async with httpx.AsyncClient() as client:
        try:
            api_url = f"{VESSEL_API_BASE_URL}/vessels/{vessel_id}/sensors/"
            response = await client.get(api_url)
            response.raise_for_status()
            # Możesz chcieć przefiltrować odpowiedź, aby zwracać tylko potrzebne pola (id, name, measurement_unit)
            # sensors_data = [{"id": s["id"], "name": s["name"], "measurement_unit": s.get("measurement_unit")} for s in response.json()]
            # return JSONResponse(content=sensors_data, status_code=response.status_code)
            return JSONResponse(
                content=response.json(), status_code=response.status_code
            )
        except httpx.HTTPStatusError as e:
            return JSONResponse(
                content=e.response.json()
                if e.response.content
                and e.response.headers.get("content-type") == "application/json"
                else {"detail": e.response.text},
                status_code=e.response.status_code,
            )
        except Exception as e:
            return JSONResponse(
                content={
                    "detail": f"Proxy error fetching sensors for vessel {vessel_id}: {str(e)}"
                },
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@router.get(
    "/api/sensors/{sensor_id}/readings",  # Ścieżka np. /sensors-overview/api/sensors/101/readings
    response_class=JSONResponse,
    name="proxy_public_get_sensor_readings",
    summary="Proxy to fetch readings for a specific sensor",
)
async def proxy_public_get_sensor_readings(
    sensor_id: int,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    # Możesz dodać skip/limit, jeśli JS ma obsługiwać paginację dla bardzo dużych zestawów danych
):
    async with httpx.AsyncClient() as client:
        try:
            params = {}
            if start_time:
                params["start_time"] = start_time.isoformat()
            if end_time:
                params["end_time"] = end_time.isoformat()
            # Domyślnie pobierzemy duży limit, np. 5000 odczytów, aby wykres był pełny
            # Backend API ma domyślny limit 1000, ale pozwala na max 5000.
            params["limit"] = str(5000)  # Ustawiamy duży limit

            # Zakładamy, że API backendu ma publiczny endpoint /public/sensors/{id}/readings/
            # Zgodnie z Twoim app/routes/sensor_readings.py, ścieżka to /sensors/{sensor_id}/readings/
            # Jeśli ten router w backendzie jest pod /public, to będzie /public/sensors/...
            # Na razie zakładam, że jest to /public/sensors/{sensor_id}/readings/
            api_url = f"{VESSEL_API_BASE_URL}/sensors/{sensor_id}/readings/"  # Upewnij się, że ścieżka jest poprawna

            response = await client.get(api_url, params=params)
            response.raise_for_status()
            return JSONResponse(
                content=response.json(), status_code=response.status_code
            )
        except httpx.HTTPStatusError as e:
            return JSONResponse(
                content=e.response.json()
                if e.response.content
                and e.response.headers.get("content-type") == "application/json"
                else {"detail": e.response.text},
                status_code=e.response.status_code,
            )
        except Exception as e:
            return JSONResponse(
                content={
                    "detail": f"Proxy error fetching readings for sensor {sensor_id}: {str(e)}"
                },
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
