from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
import httpx
import os
import json
from typing import Optional
from datetime import datetime

from pa_app.routers.login import get_current_active_user
from pa_app.utils.utils import templates

VESSEL_API_BASE_URL = os.getenv("VESSEL_API_URL")

router = APIRouter(
    prefix="/admin/sensor-classes",
    tags=["Admin - Sensor Classes Management"],
    dependencies=[Depends(get_current_active_user)],
)


@router.get("/", response_class=HTMLResponse, name="admin_serve_sensor_classes_list")
async def serve_sensor_classes_list_admin(request: Request):
    success_message = request.session.pop("flash_success", None)
    error_message = request.session.pop("flash_error", None)
    sensor_classes_list = []
    api_error_load = None
    current_year = datetime.now().year

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{VESSEL_API_BASE_URL}/sensor-classes/")
            response.raise_for_status()
            sensor_classes_list = response.json()
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
        "admin/sensor_classes_list.html",
        {
            "request": request,
            "sensor_classes_list": sensor_classes_list,
            "api_error_load": api_error_load,
            "success_message": success_message,
            "error_message": error_message,
            "current_year": current_year,
        },
    )


@router.get(
    "/new", response_class=HTMLResponse, name="admin_serve_create_sensor_class_form"
)
async def serve_create_sensor_class_form_admin(request: Request):
    form_error = request.session.pop("form_error", None)
    form_data = request.session.pop("form_data", {})
    current_year = datetime.now().year
    return templates.TemplateResponse(
        "admin/sensor_classes_form.html",
        {
            "request": request,
            "form_title": "Dodaj Nową Klasę Czujnika",
            "form_action_url": request.url_for(
                "admin_handle_create_sensor_class_proxy"
            ),
            "submit_button_text": "Dodaj Klasę Czujnika",
            "sensor_class": form_data or {},
            "api_error": form_error,
            "current_year": current_year,
        },
    )


@router.post("/new", name="admin_handle_create_sensor_class_proxy")
async def handle_create_sensor_class_proxy_admin(
    request: Request, name: str = Form(...), description: Optional[str] = Form(None)
):
    api_data = {"name": name, "description": description}
    form_data_for_retry = {"name": name, "description": description}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{VESSEL_API_BASE_URL}/sensor-classes/", json=api_data
            )
            response.raise_for_status()
            request.session["flash_success"] = (
                "Klasa czujnika została pomyślnie dodana."
            )
        except httpx.HTTPStatusError as e:
            detail = (
                e.response.json().get("detail", e.response.text)
                if e.response
                else e.response.text
            )
            if (
                e.response.status_code == 400 or e.response.status_code == 422
            ):  # Błąd walidacji lub biznesowy
                request.session["form_error"] = f"Błąd API: {detail}"
                request.session["form_data"] = form_data_for_retry
                return RedirectResponse(
                    request.url_for("admin_serve_create_sensor_class_form"),
                    status_code=status.HTTP_303_SEE_OTHER,
                )
            request.session["flash_error"] = (
                f"Błąd API ({e.response.status_code}): {detail}"
            )
        except Exception as e:
            request.session["flash_error"] = f"Nieoczekiwany błąd: {str(e)}"

    return RedirectResponse(
        request.url_for("admin_serve_sensor_classes_list"),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get(
    "/{sensor_class_id}/edit",
    response_class=HTMLResponse,
    name="admin_serve_edit_sensor_class_form",
)
async def serve_edit_sensor_class_form_admin(request: Request, sensor_class_id: int):
    sensor_class_data = request.session.pop(f"form_data_edit_{sensor_class_id}", None)
    api_error_form = request.session.pop(f"form_error_edit_{sensor_class_id}", None)
    current_year = datetime.now().year

    if not sensor_class_data:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{VESSEL_API_BASE_URL}/sensor-classes/{sensor_class_id}"
                )
                response.raise_for_status()
                sensor_class_data = response.json()
            except httpx.HTTPStatusError as e:
                detail = (
                    e.response.json().get("detail", e.response.text)
                    if e.response
                    else e.response.text
                )
                request.session["flash_error"] = (
                    f"Nie można załadować klasy czujnika (ID: {sensor_class_id}). Błąd API ({e.response.status_code}): {detail}"
                )
                return RedirectResponse(
                    request.url_for("admin_serve_sensor_classes_list"),
                    status_code=status.HTTP_303_SEE_OTHER,
                )
            except Exception as e:
                request.session["flash_error"] = (
                    f"Nieoczekiwany błąd ładowania klasy czujnika (ID: {sensor_class_id}): {str(e)}"
                )
                return RedirectResponse(
                    request.url_for("admin_serve_sensor_classes_list"),
                    status_code=status.HTTP_303_SEE_OTHER,
                )

    return templates.TemplateResponse(
        "admin/sensor_classes_form.html",
        {
            "request": request,
            "form_title": f"Edytuj Klasę Czujnika: {sensor_class_data.get('name', '')}",
            "form_action_url": request.url_for(
                "admin_handle_edit_sensor_class_proxy", sensor_class_id=sensor_class_id
            ),
            "submit_button_text": "Zapisz Zmiany",
            "sensor_class": sensor_class_data,
            "api_error": api_error_form,
            "current_year": current_year,
        },
    )


@router.post("/{sensor_class_id}/edit", name="admin_handle_edit_sensor_class_proxy")
async def handle_edit_sensor_class_proxy_admin(
    request: Request,
    sensor_class_id: int,
    name: str = Form(...),
    description: Optional[str] = Form(None),
):
    api_data = {"name": name, "description": description}
    form_data_for_retry = {
        "id": sensor_class_id,
        "name": name,
        "description": description,
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.put(
                f"{VESSEL_API_BASE_URL}/sensor-classes/{sensor_class_id}", json=api_data
            )
            response.raise_for_status()
            request.session["flash_success"] = (
                f"Klasa czujnika (ID: {sensor_class_id}) została pomyślnie zaktualizowana."
            )
        except httpx.HTTPStatusError as e:
            detail = (
                e.response.json().get("detail", e.response.text)
                if e.response
                else e.response.text
            )
            if e.response.status_code == 400 or e.response.status_code == 422:
                request.session[f"form_error_edit_{sensor_class_id}"] = (
                    f"Błąd API: {detail}"
                )
                request.session[f"form_data_edit_{sensor_class_id}"] = (
                    form_data_for_retry
                )
                return RedirectResponse(
                    request.url_for(
                        "admin_serve_edit_sensor_class_form",
                        sensor_class_id=sensor_class_id,
                    ),
                    status_code=status.HTTP_303_SEE_OTHER,
                )
            request.session["flash_error"] = (
                f"Błąd API ({e.response.status_code}): {detail}"
            )
        except Exception as e:
            request.session["flash_error"] = f"Nieoczekiwany błąd: {str(e)}"

    return RedirectResponse(
        request.url_for("admin_serve_sensor_classes_list"),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/{sensor_class_id}/delete", name="admin_handle_delete_sensor_class_proxy")
async def handle_delete_sensor_class_proxy_admin(
    request: Request, sensor_class_id: int
):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(
                f"{VESSEL_API_BASE_URL}/sensor-classes/{sensor_class_id}"
            )
            if response.status_code == status.HTTP_204_NO_CONTENT:
                request.session["flash_success"] = (
                    f"Klasa czujnika (ID: {sensor_class_id}) została pomyślnie usunięta."
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
                f"Błąd usuwania ({e.response.status_code}): {detail}"
            )
        except Exception as e:
            request.session["flash_error"] = (
                f"Nieoczekiwany błąd podczas usuwania: {str(e)}"
            )

    return RedirectResponse(
        request.url_for("admin_serve_sensor_classes_list"),
        status_code=status.HTTP_303_SEE_OTHER,
    )
