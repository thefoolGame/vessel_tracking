from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
import httpx
import os
import json
from typing import Optional, List  # Dodano List
from datetime import datetime

from pa_app.routers.login import get_current_active_user
from pa_app.utils.utils import templates

VESSEL_API_BASE_URL = os.getenv("VESSEL_API_URL")

router = APIRouter(
    prefix="/admin/fleets",
    tags=["Admin - Fleets Management"],
    dependencies=[Depends(get_current_active_user)],
)


async def _fetch_operators_for_select(client: httpx.AsyncClient) -> List[dict]:
    """Pomocnicza funkcja do pobierania operatorów dla selecta."""
    try:
        ops_response = await client.get(
            f"{VESSEL_API_BASE_URL}/fleets/utils/operators-for-select"
        )  # Użyj nowego endpointu
        ops_response.raise_for_status()
        return ops_response.json()
    except Exception as e:
        print(f"Error fetching operators for select: {e}")
        return []


@router.get("/", response_class=HTMLResponse, name="admin_serve_fleets_list")
async def serve_fleets_list_admin(request: Request):
    success_message = request.session.pop("flash_success", None)
    error_message = request.session.pop("flash_error", None)
    fleets_list = []
    api_error_load = None
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{VESSEL_API_BASE_URL}/fleets/")
            response.raise_for_status()
            fleets_list = response.json()
        except Exception as e:
            api_error_load = f"Błąd ładowania listy flot: {str(e)}"
    return templates.TemplateResponse(
        "admin/fleets_list.html",
        {
            "request": request,
            "fleets_list": fleets_list,
            "api_error_load": api_error_load,
            "success_message": success_message,
            "error_message": error_message,
            "current_year": datetime.now().year,
        },
    )


@router.get("/new", response_class=HTMLResponse, name="admin_serve_create_fleet_form")
async def serve_create_fleet_form_admin(request: Request):
    async with httpx.AsyncClient() as client:
        operators = await _fetch_operators_for_select(client)
    return templates.TemplateResponse(
        "admin/fleets_form.html",
        {
            "request": request,
            "form_title": "Dodaj Nową Flotę",
            "form_action_url": request.url_for("admin_handle_create_fleet_proxy"),
            "submit_button_text": "Dodaj Flotę",
            "fleet": {},
            "operators_for_select": operators,
            "current_year": datetime.now().year,
        },
    )


@router.post("/new", name="admin_handle_create_fleet_proxy")
async def handle_create_fleet_proxy_admin(
    request: Request,
    name: str = Form(...),
    operator_id: int = Form(...),
    description: Optional[str] = Form(None),
):
    api_data = {"name": name, "operator_id": operator_id, "description": description}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{VESSEL_API_BASE_URL}/fleets/", json=api_data
            )
            response.raise_for_status()
            request.session["flash_success"] = "Flota została pomyślnie dodana."
        except httpx.HTTPStatusError as e:
            detail = e.response.json().get("detail", e.response.text)
            if (
                e.response.status_code == 422 or e.response.status_code == 400
            ):  # Błąd walidacji lub np. nieistniejący operator
                operators = await _fetch_operators_for_select(client)
                return templates.TemplateResponse(
                    "admin/fleets_form.html",
                    {
                        "request": request,
                        "form_title": "Dodaj Nową Flotę",
                        "form_action_url": request.url_for(
                            "admin_handle_create_fleet_proxy"
                        ),
                        "submit_button_text": "Dodaj Flotę",
                        "fleet": api_data,  # Przekaż dane z formularza
                        "operators_for_select": operators,
                        "api_error": f"Błąd API ({e.response.status_code}): {detail}",
                        "current_year": datetime.now().year,
                    },
                )
            request.session["flash_error"] = (
                f"Błąd API ({e.response.status_code}): {detail}"
            )
        except Exception as e:
            request.session["flash_error"] = f"Nieoczekiwany błąd: {str(e)}"
    return RedirectResponse(
        request.url_for("admin_serve_fleets_list"),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get(
    "/{fleet_id}/edit", response_class=HTMLResponse, name="admin_serve_edit_fleet_form"
)
async def serve_edit_fleet_form_admin(request: Request, fleet_id: int):
    async with httpx.AsyncClient() as client:
        fleet_data = request.session.pop(f"form_data_fleet_edit_{fleet_id}", None)
        api_error_form = request.session.pop(f"form_error_fleet_edit_{fleet_id}", None)
        operators = await _fetch_operators_for_select(client)

        if (
            not fleet_data
        ):  # Jeśli nie ma danych z sesji (np. po błędzie), pobierz z API
            try:
                response = await client.get(f"{VESSEL_API_BASE_URL}/fleets/{fleet_id}")
                response.raise_for_status()
                fleet_data = response.json()
            except Exception as e:
                request.session["flash_error"] = (
                    f"Nie można załadować floty (ID: {fleet_id}) do edycji: {str(e)}"
                )
                return RedirectResponse(
                    request.url_for("admin_serve_fleets_list"),
                    status_code=status.HTTP_303_SEE_OTHER,
                )

    return templates.TemplateResponse(
        "admin/fleets_form.html",
        {
            "request": request,
            "form_title": f"Edytuj Flotę: {fleet_data.get('name', '')}",
            "form_action_url": request.url_for(
                "admin_handle_edit_fleet_proxy", fleet_id=fleet_id
            ),
            "submit_button_text": "Zapisz Zmiany",
            "fleet": fleet_data,
            "operators_for_select": operators,
            "api_error": api_error_form,
            "current_year": datetime.now().year,
        },
    )


@router.post("/{fleet_id}/edit", name="admin_handle_edit_fleet_proxy")
async def handle_edit_fleet_proxy_admin(
    request: Request,
    fleet_id: int,
    name: str = Form(...),
    operator_id: int = Form(...),
    description: Optional[str] = Form(None),
):
    api_data = {"name": name, "operator_id": operator_id, "description": description}
    form_data_for_retry = {"id": fleet_id, **api_data}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.put(
                f"{VESSEL_API_BASE_URL}/fleets/{fleet_id}", json=api_data
            )
            response.raise_for_status()
            request.session["flash_success"] = (
                f"Dane floty (ID: {fleet_id}) zostały pomyślnie zaktualizowane."
            )
        except httpx.HTTPStatusError as e:
            detail = e.response.json().get("detail", e.response.text)
            if e.response.status_code == 422 or e.response.status_code == 400:
                request.session[f"form_error_fleet_edit_{fleet_id}"] = (
                    f"Błąd API ({e.response.status_code}): {detail}"
                )
                request.session[f"form_data_fleet_edit_{fleet_id}"] = (
                    form_data_for_retry
                )
                return RedirectResponse(
                    request.url_for("admin_serve_edit_fleet_form", fleet_id=fleet_id),
                    status_code=status.HTTP_303_SEE_OTHER,
                )
            request.session["flash_error"] = (
                f"Błąd API ({e.response.status_code}): {detail}"
            )
        except Exception as e:
            request.session["flash_error"] = f"Nieoczekiwany błąd: {str(e)}"
    return RedirectResponse(
        request.url_for("admin_serve_fleets_list"),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/{fleet_id}/delete", name="admin_handle_delete_fleet_proxy")
async def handle_delete_fleet_proxy_admin(request: Request, fleet_id: int):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(f"{VESSEL_API_BASE_URL}/fleets/{fleet_id}")
            response.raise_for_status()  # Sprawdzi 204 lub rzuci błąd dla 4xx/5xx
            request.session["flash_success"] = (
                f"Flota (ID: {fleet_id}) została pomyślnie usunięta."
            )
        except httpx.HTTPStatusError as e:
            detail = e.response.json().get("detail", e.response.text)
            request.session["flash_error"] = (
                f"Błąd usuwania floty (status: {e.response.status_code}): {detail}"
            )
        except Exception as e:
            request.session["flash_error"] = (
                f"Nieoczekiwany błąd podczas usuwania floty: {str(e)}"
            )
    return RedirectResponse(
        request.url_for("admin_serve_fleets_list"),
        status_code=status.HTTP_303_SEE_OTHER,
    )
