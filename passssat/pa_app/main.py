import socket
import os
import httpx
import csv

from datetime import datetime
from decimal import Decimal

from fastapi import FastAPI, Request, HTTPException, status, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from pydantic import BaseModel

from pa_app.routers import login, charts, connect, sensors_page
from pa_app.routers.admin import (
    manufacturers,
    operators,
    fleets,
    vessel_types,
    sensor_classes,
    sensor_types,
    vessels,
    vessel_sensors,
    vessel_routes,
    vessel_locations,
)
from pa_app.utils.utils import templates


VESSEL_API_BASE_URL = os.getenv("VESSEL_API_URL")

if not VESSEL_API_BASE_URL:
    print("WEB_APP: UWAGA! Zmienna środowiskowa VESSEL_API_URL nie jest ustawiona.")

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="ZMIEN_MNIE_NA_PRAWDZIWY_LOSOWY_KLUCZ")


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    # Sprawdź, czy to błąd 401 (Not authenticated)
    # ORAZ czy żądanie prawdopodobnie oczekuje HTML (np. nie jest to żądanie API z nagłówkiem Accept: application/json)
    # Można to uprościć lub uczynić bardziej precyzyjnym
    accept_header = request.headers.get("accept", "").lower()
    is_html_expected = (
        "text/html" in accept_header or "*" in accept_header
    )  # Uproszczone sprawdzenie

    if exc.status_code == status.HTTP_401_UNAUTHORIZED and is_html_expected:
        # Przekieruj na stronę logowania, zachowując oryginalny URL jako parametr 'next'
        # aby móc wrócić po zalogowaniu
        login_url = request.url_for(
            "login_page"
        )  # Użyj nazwy endpointu strony logowania
        # Możesz dodać oryginalny URL jako parametr 'next'
        # next_url = str(request.url)
        # return RedirectResponse(url=f"{login_url}?next={next_url}", status_code=status.HTTP_302_FOUND)
        # Na razie proste przekierowanie:
        return RedirectResponse(url=login_url, status_code=status.HTTP_302_FOUND)
    else:
        # Dla innych błędów HTTP lub żądań API, użyj domyślnej obsługi FastAPI/Starlette
        # Można by tu zwrócić standardową odpowiedź JSON, jeśli to API
        if "application/json" in accept_header and not is_html_expected:
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
                headers=exc.headers,
            )
        # Domyślnie, jeśli nie jest to JSON, można zwrócić prosty HTML
        return HTMLResponse(
            content=f"<html><body><h1>{exc.status_code} Error</h1><p>{exc.detail}</p></body></html>",
            status_code=exc.status_code,
            headers=exc.headers,
        )


app.include_router(login.router)
app.include_router(charts.router, prefix="/sensors", tags=["Sensors"])
app.include_router(connect.router)
app.include_router(manufacturers.router)
app.include_router(operators.router)
app.include_router(fleets.router)
app.include_router(vessel_types.router)
app.include_router(sensor_classes.router)
app.include_router(sensor_types.router)
app.include_router(vessels.router)
app.include_router(vessel_sensors.router)
app.include_router(vessel_routes.router)
app.include_router(vessel_locations.router)
app.include_router(sensors_page.router)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
async def startup_event():
    app.state.httpx_client = httpx.AsyncClient()
    print("WEB_APP: Aplikacja PassAt startuje. Klient HTTPX zainicjalizowany.")


@app.on_event("shutdown")
async def shutdown_event():
    await app.state.httpx_client.aclose()
    print("WEB_APP: Aplikacja PassAt zamyka się. Klient HTTPX zamknięty.")


@app.get("/", response_class=HTMLResponse, name="map_page")
def index(request: Request):
    context = {"request": request}
    return templates.TemplateResponse("index.html", context)


@app.post("/reload", response_class=HTMLResponse)
async def save_message(request: Request):
    context = {"request": request}
    return templates.TemplateResponse("index.html", context)


@app.get(
    "/map-data/initial-vessels-public",
    response_class=JSONResponse,
    name="get_public_initial_map_data",
    summary="Proxy to fetch public initial map data (vessels, positions, planned routes)",
)
async def proxy_get_public_initial_map_data():
    async with httpx.AsyncClient() as client:
        try:
            api_url = f"{VESSEL_API_BASE_URL}/public/map/initial-vessels"
            response = await client.get(api_url)
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
                content={"detail": f"Proxy error fetching public map data: {str(e)}"},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@app.get(
    "/public/vessels/{vessel_id}",
    response_class=JSONResponse,
    name="public_proxy_get_vessel_details",
    summary="Proxy to fetch public details for a specific vessel",
)
async def public_proxy_get_vessel_details(vessel_id: int):
    async with httpx.AsyncClient() as client:
        try:
            api_url = f"{VESSEL_API_BASE_URL}/vessels/{vessel_id}"
            response = await client.get(api_url)
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
                    "detail": f"Proxy error fetching public vessel details: {str(e)}"
                },
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@app.get(
    "/public/vessels/{vessel_id}/locations",
    response_class=JSONResponse,
    name="public_proxy_get_vessel_locations",
    summary="Proxy to fetch public location history for a specific vessel",
)
async def public_proxy_get_vessel_locations(
    vessel_id: int,
    skip: int = Query(0),
    limit: int = Query(50),
    # start_time: Optional[datetime] = Query(None), # Jeśli potrzebujesz filtrowania po czasie
    # end_time: Optional[datetime] = Query(None),   # Jeśli potrzebujesz filtrowania po czasie
):
    async with httpx.AsyncClient() as client:
        try:
            params = {"skip": str(skip), "limit": str(limit)}
            # if start_time: params["start_time"] = start_time.isoformat()
            # if end_time: params["end_time"] = end_time.isoformat()

            api_url = f"{VESSEL_API_BASE_URL}/vessels/{vessel_id}/locations/"
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
                    "detail": f"Proxy error fetching public vessel locations: {str(e)}"
                },
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
