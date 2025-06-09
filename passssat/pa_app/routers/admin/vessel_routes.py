from fastapi import APIRouter, Request, Depends, HTTPException, status, Body, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
import httpx
import os
from typing import Optional, Dict, Any, List

from pa_app.routers.login import get_current_active_user
from pa_app.utils.utils import templates

VESSEL_API_BASE_URL = os.getenv("VESSEL_API_URL")

router = APIRouter(
    prefix="/admin/vessels/{vessel_id}/route-management",
    tags=["Admin - Vessel Route Management"],
    dependencies=[Depends(get_current_active_user)],
)


# --- Istniejące funkcje pomocnicze i endpoint GET / ---
async def fetch_vessel_details_for_route(
    client: httpx.AsyncClient, vessel_id: int
) -> Optional[Dict[str, Any]]:
    try:
        response = await client.get(f"{VESSEL_API_BASE_URL}/vessels/{vessel_id}")
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


@router.get(
    "/",
    response_class=HTMLResponse,
    name="admin_serve_vessel_route_management",
)
async def serve_vessel_route_management_page(
    request: Request,
    vessel_id: int,
):
    async with httpx.AsyncClient() as client:
        vessel_details = await fetch_vessel_details_for_route(client, vessel_id)
        if not vessel_details:
            request.session["flash_error"] = f"Nie znaleziono statku o ID: {vessel_id}."
            return RedirectResponse(
                request.url_for("admin_serve_vessels_list"),
                status_code=status.HTTP_303_SEE_OTHER,
            )

    return templates.TemplateResponse(
        "admin/vessel_route_management.html",
        {
            "request": request,
            "vessel": vessel_details,
            "page_title": f"Zarządzanie Trasą dla Statku: {vessel_details.get('name', '')}",
        },
    )


# --- NOWE ENDPOINTY PROXY DLA ROUTE POINTS ---


@router.get(
    "/points/",  # Ścieżka: /admin/vessels/{vessel_id}/route-management/points/
    response_class=JSONResponse,
    name="proxy_get_route_points",
)
async def proxy_get_route_points_for_vessel(vessel_id: int):
    async with httpx.AsyncClient() as client:
        try:
            # Wywołanie API backendu
            api_url = f"{VESSEL_API_BASE_URL}/vessels/{vessel_id}/route-points/"
            response = await client.get(api_url)
            response.raise_for_status()  # Rzuci błąd dla statusów 4xx/5xx
            return JSONResponse(
                content=response.json(), status_code=response.status_code
            )
        except httpx.HTTPStatusError as e:
            # Przekaż błąd z backendu do frontendu
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
    "/points/",  # Ścieżka: /admin/vessels/{vessel_id}/route-management/points/
    response_class=JSONResponse,
    name="proxy_create_route_point",
)
async def proxy_create_route_point_for_vessel(
    vessel_id: int, payload: Dict[Any, Any] = Body(...)
):
    async with httpx.AsyncClient() as client:
        try:
            api_url = f"{VESSEL_API_BASE_URL}/vessels/{vessel_id}/route-points/"
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


@router.put(
    "/points/{route_point_id}",  # Ścieżka: /admin/vessels/{vessel_id}/route-management/points/{route_point_id}
    response_class=JSONResponse,
    name="proxy_update_route_point",
)
async def proxy_update_route_point_for_vessel(
    vessel_id: int, route_point_id: int, payload: Dict[Any, Any] = Body(...)
):
    async with httpx.AsyncClient() as client:
        try:
            api_url = f"{VESSEL_API_BASE_URL}/vessels/{vessel_id}/route-points/{route_point_id}"
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
    "/points/{route_point_id}",  # Ścieżka: /admin/vessels/{vessel_id}/route-management/points/{route_point_id}
    response_class=JSONResponse,
    name="proxy_delete_route_point",
)
async def proxy_delete_route_point_for_vessel(vessel_id: int, route_point_id: int):
    async with httpx.AsyncClient() as client:
        try:
            api_url = f"{VESSEL_API_BASE_URL}/vessels/{vessel_id}/route-points/{route_point_id}"
            response = await client.delete(api_url)
            # DELETE może zwrócić 204 No Content, co jest OK
            if response.status_code == status.HTTP_204_NO_CONTENT:
                return JSONResponse(
                    content=None, status_code=status.HTTP_204_NO_CONTENT
                )
            response.raise_for_status()  # Dla innych błędów
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
    "/points/reorder",  # Ścieżka: /admin/vessels/{vessel_id}/route-management/points/reorder
    response_class=JSONResponse,
    name="proxy_reorder_route_points",
)
async def proxy_reorder_route_points_for_vessel(
    vessel_id: int, ordered_ids: List[int] = Body(...)
):
    async with httpx.AsyncClient() as client:
        try:
            # [założenie] Endpoint w backendzie API to /vessels/{vessel_id}/route-points/reorder
            # i przyjmuje listę ID w ciele żądania.
            api_url = f"{VESSEL_API_BASE_URL}/vessels/{vessel_id}/route-points/reorder"
            response = await client.post(api_url, json=ordered_ids)  # Wysyłamy listę ID
            response.raise_for_status()
            # Endpoint reorder może zwracać zaktualizowaną listę punktów lub tylko status sukcesu
            return JSONResponse(
                content=response.json() if response.content else None,
                status_code=response.status_code,
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


# Endpoint do pobierania aktualnej pozycji statku (jeśli potrzebny dla mapy trasy)
@router.get(
    "/current-position/",  # Ścieżka: /admin/vessels/{vessel_id}/route-management/current-position/
    response_class=JSONResponse,
    name="proxy_get_vessel_current_location",
)
async def proxy_get_vessel_current_location(vessel_id: int):
    async with httpx.AsyncClient() as client:
        try:
            api_url = f"{VESSEL_API_BASE_URL}/vessels/{vessel_id}/locations/latest"

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


@router.get(
    "/points/{route_point_id}",  # Ścieżka: /admin/vessels/{vessel_id}/route-management/points/{route_point_id}
    response_class=JSONResponse,
    name="proxy_get_single_route_point",  # Nazwa dla JS, jeśli potrzebna
)
async def proxy_get_single_route_point_for_vessel(vessel_id: int, route_point_id: int):
    async with httpx.AsyncClient() as client:
        try:
            # Wywołanie API backendu
            api_url = f"{VESSEL_API_BASE_URL}/vessels/{vessel_id}/route-points/{route_point_id}"
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
                content={"detail": f"Proxy error: {str(e)}"},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
