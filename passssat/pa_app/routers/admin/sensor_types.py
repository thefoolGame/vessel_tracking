from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
import httpx
import os
import json
from typing import Optional, List, Dict, Any  # Dodano List, Dict, Any
from datetime import datetime

from pa_app.routers.login import get_current_active_user
from pa_app.utils.utils import templates

VESSEL_API_BASE_URL = os.getenv("VESSEL_API_URL")

router = APIRouter(
    prefix="/admin/sensor-types",
    tags=["Admin - Sensor Types Management"],
    dependencies=[Depends(get_current_active_user)],
)


async def fetch_manufacturers_for_dropdown(
    client: httpx.AsyncClient,
) -> List[Dict[str, Any]]:
    try:
        response = await client.get(
            f"{VESSEL_API_BASE_URL}/manufacturers/?limit=1000"
        )  # Pobierz wszystkich
        response.raise_for_status()
        return response.json()
    except Exception:
        return []


async def fetch_sensor_classes_for_dropdown(
    client: httpx.AsyncClient,
) -> List[Dict[str, Any]]:
    try:
        # Upewnij się, że masz endpoint /sensor-classes/ w głównym API
        response = await client.get(f"{VESSEL_API_BASE_URL}/sensor-classes/?limit=1000")
        response.raise_for_status()
        return response.json()
    except Exception:
        return []


@router.get("/", response_class=HTMLResponse, name="admin_serve_sensor_types_list")
async def serve_sensor_types_list_admin(request: Request):
    sensor_types_list = []
    api_error_load = None
    success_message = request.session.pop("flash_success", None)
    error_message = request.session.pop("flash_error", None)
    current_year = datetime.now().year

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{VESSEL_API_BASE_URL}/sensor-types/")
            response.raise_for_status()
            sensor_types_list = response.json()
        except httpx.HTTPStatusError as e:
            detail = (
                e.response.json().get("detail", e.response.text)
                if e.response
                else e.response.text
            )
            api_error_load = f"Błąd API ({e.response.status_code}): {detail}"
        except Exception as e:
            api_error_load = f"Nieoczekiwany błąd: {str(e)}"

    return templates.TemplateResponse(
        "admin/sensor_types_list.html",
        {
            "request": request,
            "sensor_types_list": sensor_types_list,
            "api_error_load": api_error_load,
            "success_message": success_message,
            "error_message": error_message,
            "current_year": current_year,
        },
    )


@router.get(
    "/new", response_class=HTMLResponse, name="admin_serve_create_sensor_type_form"
)
async def serve_create_sensor_type_form_admin(request: Request):
    async with httpx.AsyncClient() as client:
        manufacturers = await fetch_manufacturers_for_dropdown(client)
        sensor_classes = await fetch_sensor_classes_for_dropdown(client)

    form_error = request.session.pop("form_error", None)
    form_data = request.session.pop("form_data", {})
    current_year = datetime.now().year

    return templates.TemplateResponse(
        "admin/sensor_types_form.html",
        {
            "request": request,
            "form_title": "Dodaj Nowy Typ Czujnika",
            "form_action_url": request.url_for("admin_handle_create_sensor_type_proxy"),
            "submit_button_text": "Dodaj Typ Czujnika",
            "sensor_type": form_data or {},
            "manufacturers": manufacturers,
            "sensor_classes": sensor_classes,
            "api_error": form_error,
            "current_year": current_year,
        },
    )


@router.post("/new", name="admin_handle_create_sensor_type_proxy")
async def handle_create_sensor_type_proxy_admin(
    request: Request,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    sensor_class_id: int = Form(...),
    manufacturer_id: Optional[int] = Form(None),
):
    api_data = {
        "name": name,
        "description": description,
        "sensor_class_id": sensor_class_id,
        "manufacturer_id": manufacturer_id
        if manufacturer_id
        else None,  # Przekaż None, jeśli nie wybrano
    }
    form_data_for_retry = api_data.copy()  # Do ponownego wypełnienia formularza

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{VESSEL_API_BASE_URL}/sensor-types/", json=api_data
            )
            response.raise_for_status()
            request.session["flash_success"] = "Typ czujnika został pomyślnie dodany."
            return RedirectResponse(
                request.url_for("admin_serve_sensor_types_list"),
                status_code=status.HTTP_303_SEE_OTHER,
            )
        except httpx.HTTPStatusError as e:
            detail = (
                e.response.json().get("detail", e.response.text)
                if e.response
                else e.response.text
            )
            request.session["form_error"] = (
                f"Błąd API ({e.response.status_code}): {detail}"
            )
            request.session["form_data"] = form_data_for_retry
            return RedirectResponse(
                request.url_for("admin_serve_create_sensor_type_form"),
                status_code=status.HTTP_303_SEE_OTHER,
            )
        except Exception as e:
            request.session["flash_error"] = f"Nieoczekiwany błąd: {str(e)}"
            return RedirectResponse(
                request.url_for("admin_serve_sensor_types_list"),
                status_code=status.HTTP_303_SEE_OTHER,
            )


@router.get(
    "/{sensor_type_id}/edit",
    response_class=HTMLResponse,
    name="admin_serve_edit_sensor_type_form",
)
async def serve_edit_sensor_type_form_admin(request: Request, sensor_type_id: int):
    sensor_type_data = request.session.pop(f"form_data_edit_{sensor_type_id}", None)
    api_error_form = request.session.pop(f"form_error_edit_{sensor_type_id}", None)
    manufacturers = []
    sensor_classes = []
    current_year = datetime.now().year

    async with httpx.AsyncClient() as client:
        manufacturers = await fetch_manufacturers_for_dropdown(client)
        sensor_classes = await fetch_sensor_classes_for_dropdown(client)
        if (
            not sensor_type_data
        ):  # Jeśli nie ma danych z sesji (np. po błędzie), pobierz z API
            try:
                response = await client.get(
                    f"{VESSEL_API_BASE_URL}/sensor-types/{sensor_type_id}"
                )
                response.raise_for_status()
                sensor_type_data = response.json()
            except httpx.HTTPStatusError as e:
                detail = (
                    e.response.json().get("detail", e.response.text)
                    if e.response
                    else e.response.text
                )
                request.session["flash_error"] = (
                    f"Nie można załadować typu czujnika (ID: {sensor_type_id}). Błąd API ({e.response.status_code}): {detail}"
                )
                return RedirectResponse(
                    request.url_for("admin_serve_sensor_types_list"),
                    status_code=status.HTTP_303_SEE_OTHER,
                )
            except Exception as e:
                request.session["flash_error"] = (
                    f"Nieoczekiwany błąd ładowania typu czujnika (ID: {sensor_type_id}): {str(e)}"
                )
                return RedirectResponse(
                    request.url_for("admin_serve_sensor_types_list"),
                    status_code=status.HTTP_303_SEE_OTHER,
                )

    return templates.TemplateResponse(
        "admin/sensor_types_form.html",
        {
            "request": request,
            "form_title": f"Edytuj Typ Czujnika: {sensor_type_data.get('name', '')}",
            "form_action_url": request.url_for(
                "admin_handle_edit_sensor_type_proxy", sensor_type_id=sensor_type_id
            ),
            "submit_button_text": "Zapisz Zmiany",
            "sensor_type": sensor_type_data,
            "manufacturers": manufacturers,
            "sensor_classes": sensor_classes,
            "api_error": api_error_form,
            "current_year": current_year,
        },
    )


@router.post("/{sensor_type_id}/edit", name="admin_handle_edit_sensor_type_proxy")
async def handle_edit_sensor_type_proxy_admin(
    request: Request,
    sensor_type_id: int,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    sensor_class_id: int = Form(...),
    manufacturer_id: Optional[int] = Form(None),
):
    api_data = {
        "name": name,
        "description": description,
        "sensor_class_id": sensor_class_id,
        "manufacturer_id": manufacturer_id if manufacturer_id else None,
    }
    form_data_for_retry = api_data.copy()
    form_data_for_retry["id"] = sensor_type_id  # Dla ponownego wypełnienia formularza

    async with httpx.AsyncClient() as client:
        try:
            response = await client.put(
                f"{VESSEL_API_BASE_URL}/sensor-types/{sensor_type_id}", json=api_data
            )
            response.raise_for_status()
            request.session["flash_success"] = (
                f"Typ czujnika (ID: {sensor_type_id}) został pomyślnie zaktualizowany."
            )
            return RedirectResponse(
                request.url_for("admin_serve_sensor_types_list"),
                status_code=status.HTTP_303_SEE_OTHER,
            )
        except httpx.HTTPStatusError as e:
            detail = (
                e.response.json().get("detail", e.response.text)
                if e.response
                else e.response.text
            )
            request.session[f"form_error_edit_{sensor_type_id}"] = (
                f"Błąd API ({e.response.status_code}): {detail}"
            )
            request.session[f"form_data_edit_{sensor_type_id}"] = form_data_for_retry
            return RedirectResponse(
                request.url_for(
                    "admin_serve_edit_sensor_type_form", sensor_type_id=sensor_type_id
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )
        except Exception as e:
            request.session["flash_error"] = f"Nieoczekiwany błąd: {str(e)}"
            return RedirectResponse(
                request.url_for("admin_serve_sensor_types_list"),
                status_code=status.HTTP_303_SEE_OTHER,
            )


@router.post("/{sensor_type_id}/delete", name="admin_handle_delete_sensor_type_proxy")
async def handle_delete_sensor_type_proxy_admin(request: Request, sensor_type_id: int):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(
                f"{VESSEL_API_BASE_URL}/sensor-types/{sensor_type_id}"
            )
            if response.status_code == status.HTTP_204_NO_CONTENT:
                request.session["flash_success"] = (
                    f"Typ czujnika (ID: {sensor_type_id}) został pomyślnie usunięty."
                )
            else:
                response.raise_for_status()
        except httpx.HTTPStatusError as e:
            detail = (
                e.response.json().get("detail", e.response.text)
                if e.response
                else e.response.text
            )
            request.session["flash_error"] = (
                f"Błąd usuwania typu czujnika (status: {e.response.status_code}): {detail}"
            )
        except Exception as e:
            request.session["flash_error"] = (
                f"Nieoczekiwany błąd podczas usuwania typu czujnika: {str(e)}"
            )
    return RedirectResponse(
        request.url_for("admin_serve_sensor_types_list"),
        status_code=status.HTTP_303_SEE_OTHER,
    )
