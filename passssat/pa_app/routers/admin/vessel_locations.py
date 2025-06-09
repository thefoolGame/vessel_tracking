from fastapi import (
    APIRouter,
    Request,
    Depends,
    HTTPException,
    status,
    Query,
    Body,
    Form,
)
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
import httpx
import os
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List

from pa_app.routers.login import get_current_active_user
from pa_app.utils.utils import templates

VESSEL_API_BASE_URL = os.getenv("VESSEL_API_URL")

router = APIRouter(
    prefix="/admin/vessels/{vessel_id}/location-history-management",
    tags=["Admin - Vessel Location History Management"],
    dependencies=[Depends(get_current_active_user)],
)


# Funkcja pomocnicza do pobierania szczegółów statku
async def fetch_vessel_details_for_location(  # Inna nazwa dla uniknięcia konfliktu
    client: httpx.AsyncClient, vessel_id: int
) -> Optional[Dict[str, Any]]:
    try:
        response = await client.get(f"{VESSEL_API_BASE_URL}/vessels/{vessel_id}")
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


@router.get(
    "/",  # Ścieżka będzie /admin/vessels/{vessel_id}/location-history-management/
    response_class=HTMLResponse,
    name="admin_serve_vessel_location_management",
)
async def serve_vessel_location_management_page(
    request: Request,
    vessel_id: int,
):
    async with httpx.AsyncClient() as client:
        vessel_details = await fetch_vessel_details_for_location(client, vessel_id)
        if not vessel_details:
            request.session["flash_error"] = f"Nie znaleziono statku o ID: {vessel_id}."
            return RedirectResponse(
                request.url_for("admin_serve_vessels_list"),
                status_code=status.HTTP_303_SEE_OTHER,
            )

    return templates.TemplateResponse(
        "admin/vessel_location_management.html",  # Nowy szablon
        {
            "request": request,
            "vessel": vessel_details,
            "page_title": f"Zarządzanie Historią Lokalizacji: {vessel_details.get('name', '')}",
            # API_BASE_URL nie jest tu bezpośrednio potrzebne, bo JS będzie wołał endpointy proxy
        },
    )


@router.get(
    "/locations/",  # Ścieżka: /admin/vessels/{vessel_id}/location-history-management/locations/
    response_class=JSONResponse,
    name="proxy_get_location_entries",
)
async def proxy_get_location_entries_for_vessel(
    vessel_id: int,
    skip: int = Query(0),
    limit: int = Query(100),  # Domyślny limit dla JS
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
):
    async with httpx.AsyncClient() as client:
        try:
            params: Dict[str, str] = {"skip": str(skip), "limit": str(limit)}
            if start_time:
                params["start_time"] = start_time.isoformat()
            if end_time:
                params["end_time"] = end_time.isoformat()

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
                else {"detail": e.response.text},
                status_code=e.response.status_code,
            )
        except Exception as e:
            return JSONResponse(
                content={"detail": f"Proxy error: {str(e)}"},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@router.post(
    "/locations/",
    response_class=JSONResponse,
    name="proxy_create_location_entry",
)
async def proxy_create_location_entry_for_vessel(
    vessel_id: int, payload: Dict[Any, Any] = Body(...)
):
    async with httpx.AsyncClient() as client:
        try:
            api_url = f"{VESSEL_API_BASE_URL}/vessels/{vessel_id}/locations/"
            response = await client.post(api_url, json=payload)
            response.raise_for_status()
            return JSONResponse(
                content=response.json(), status_code=response.status_code
            )
        except httpx.HTTPStatusError as e:
            return JSONResponse(
                content=e.response.json()
                if e.response.content
                else {"detail": e.response.text},
                status_code=e.response.status_code,
            )
        except Exception as e:
            return JSONResponse(
                content={"detail": f"Proxy error: {str(e)}"},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@router.get(
    "/locations/{location_id}",  # NOWY ENDPOINT DLA POJEDYNCZEGO WPISU
    response_class=JSONResponse,
    name="proxy_get_single_location_entry",
)
async def proxy_get_single_location_entry(vessel_id: int, location_id: int):
    async with httpx.AsyncClient() as client:
        try:
            api_url = (
                f"{VESSEL_API_BASE_URL}/vessels/{vessel_id}/locations/{location_id}"
            )
            response = await client.get(api_url)
            response.raise_for_status()
            return JSONResponse(
                content=response.json(), status_code=response.status_code
            )
        except httpx.HTTPStatusError as e:
            return JSONResponse(
                content=e.response.json()
                if e.response.content
                else {"detail": e.response.text},
                status_code=e.response.status_code,
            )
        except Exception as e:
            return JSONResponse(
                content={"detail": f"Proxy error: {str(e)}"},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@router.put(
    "/locations/{location_id}",
    response_class=JSONResponse,
    name="proxy_update_location_entry",
)
async def proxy_update_location_entry_for_vessel(
    vessel_id: int, location_id: int, payload: Dict[Any, Any] = Body(...)
):
    async with httpx.AsyncClient() as client:
        try:
            api_url = (
                f"{VESSEL_API_BASE_URL}/vessels/{vessel_id}/locations/{location_id}"
            )
            response = await client.put(api_url, json=payload)
            response.raise_for_status()
            return JSONResponse(
                content=response.json(), status_code=response.status_code
            )
        except httpx.HTTPStatusError as e:
            return JSONResponse(
                content=e.response.json()
                if e.response.content
                else {"detail": e.response.text},
                status_code=e.response.status_code,
            )
        except Exception as e:
            return JSONResponse(
                content={"detail": f"Proxy error: {str(e)}"},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@router.delete(
    "/locations/{location_id}",
    response_class=JSONResponse,
    name="proxy_delete_location_entry",
)
async def proxy_delete_location_entry_for_vessel(vessel_id: int, location_id: int):
    async with httpx.AsyncClient() as client:
        try:
            api_url = (
                f"{VESSEL_API_BASE_URL}/vessels/{vessel_id}/locations/{location_id}"
            )
            response = await client.delete(api_url)
            if response.status_code == status.HTTP_204_NO_CONTENT:
                return JSONResponse(
                    content=None, status_code=status.HTTP_204_NO_CONTENT
                )
            response.raise_for_status()
            return JSONResponse(
                content=response.json(), status_code=response.status_code
            )  # Na wypadek gdyby API zwracało ciało przy DELETE
        except httpx.HTTPStatusError as e:
            return JSONResponse(
                content=e.response.json()
                if e.response.content
                else {"detail": e.response.text},
                status_code=e.response.status_code,
            )
        except Exception as e:
            return JSONResponse(
                content={"detail": f"Proxy error: {str(e)}"},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
