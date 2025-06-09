from fastapi import APIRouter, Request, Depends, Form, HTTPException, status as f_status
from fastapi.responses import HTMLResponse, RedirectResponse
import httpx
import os
import json
from typing import Optional, List, Dict, Any
from datetime import datetime

from pa_app.routers.login import get_current_active_user
from pa_app.utils.utils import templates

VESSEL_API_BASE_URL = os.getenv("VESSEL_API_URL")

router = APIRouter(
    prefix="/admin/vessels",
    tags=["Admin - Vessels Management"],
    dependencies=[Depends(get_current_active_user)],
)


# Funkcja pomocnicza do pobierania list dla dropdownów
async def get_dropdown_data(
    client: httpx.AsyncClient,
) -> Dict[str, List[Dict[str, Any]]]:
    vessel_types = []
    operators = []
    fleets = []
    try:
        vt_response = await client.get(
            f"{VESSEL_API_BASE_URL}/vessel-types/?limit=1000"
        )
        vt_response.raise_for_status()
        vessel_types = vt_response.json()

        op_response = await client.get(f"{VESSEL_API_BASE_URL}/operators/?limit=1000")
        op_response.raise_for_status()
        operators = op_response.json()

        fl_response = await client.get(f"{VESSEL_API_BASE_URL}/fleets/?limit=1000")
        fl_response.raise_for_status()
        fleets = fl_response.json()
    except Exception as e:
        print(f"Error fetching dropdown data: {e}")  # Loguj błąd
    return {"vessel_types": vessel_types, "operators": operators, "fleets": fleets}


@router.get("/", response_class=HTMLResponse, name="admin_serve_vessels_list")
async def serve_vessels_list_admin(request: Request):
    vessels_list = []
    api_error_load = None
    success_message = request.session.pop("flash_success", None)
    error_message = request.session.pop("flash_error", None)
    current_year = datetime.now().year

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{VESSEL_API_BASE_URL}/vessels/?limit=1000"
            )  # Pobierz więcej na start
            response.raise_for_status()
            vessels_list = response.json()
        except Exception as e:
            api_error_load = f"Błąd ładowania listy statków: {str(e)}"

    return templates.TemplateResponse(
        "admin/vessels_list.html",
        {
            "request": request,
            "vessels_list": vessels_list,
            "api_error_load": api_error_load,
            "success_message": success_message,
            "error_message": error_message,
            "current_year": current_year,
        },
    )


@router.get("/new", response_class=HTMLResponse, name="admin_serve_create_vessel_form")
async def serve_create_vessel_form_admin(request: Request):
    async with httpx.AsyncClient() as client:
        dropdown_data = await get_dropdown_data(client)
    current_year = datetime.now().year
    form_error = request.session.pop("form_error", None)
    form_data = request.session.pop("form_data", {})

    return templates.TemplateResponse(
        "admin/vessels_form.html",
        {
            "request": request,
            "form_title": "Dodaj Nowy Statek",
            "form_action_url": request.url_for("admin_handle_create_vessel_proxy"),
            "submit_button_text": "Dodaj Statek",
            "vessel": form_data or {},
            "vessel_types": dropdown_data["vessel_types"],
            "operators": dropdown_data["operators"],
            "fleets": dropdown_data["fleets"],
            "api_error": form_error,
            "current_year": current_year,
        },
    )


@router.post("/new", name="admin_handle_create_vessel_proxy")
async def handle_create_vessel_proxy_admin(
    request: Request,
    name: str = Form(...),
    vessel_type_id: int = Form(...),
    operator_id: int = Form(
        ...
    ),  # Początkowo wymagane, ale może być nadpisane przez logikę floty
    fleet_id: Optional[int] = Form(None),
    production_year: Optional[int] = Form(None),
    registration_number: Optional[str] = Form(None),
    imo_number: Optional[str] = Form(None),
    mmsi_number: Optional[str] = Form(None),
    call_sign: Optional[str] = Form(None),
    status: str = Form("active"),
):
    api_data = {
        "name": name,
        "vessel_type_id": vessel_type_id,
        "operator_id": operator_id,
        "fleet_id": fleet_id,
        "production_year": production_year,
        "registration_number": registration_number,
        "imo_number": imo_number,
        "mmsi_number": mmsi_number,
        "call_sign": call_sign,
        "status": status,
    }
    # Usuń klucze z None, aby nie wysyłać ich, jeśli API ich nie oczekuje jako null
    api_data_cleaned = {k: v for k, v in api_data.items() if v is not None}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{VESSEL_API_BASE_URL}/vessels/", json=api_data_cleaned
            )
            response.raise_for_status()
            request.session["flash_success"] = "Statek został pomyślnie dodany."
            return RedirectResponse(
                request.url_for("admin_serve_vessels_list"),
                status_code=f_status.HTTP_303_SEE_OTHER,
            )
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json().get("detail", str(e.response.content))
            except json.JSONDecodeError:
                detail = str(e.response.content)

            request.session["form_error"] = (
                f"Błąd API ({e.response.status_code}): {detail}"
            )
            request.session["form_data"] = (
                api_data  # Zapisz oryginalne dane do ponownego wypełnienia
            )
            return RedirectResponse(
                request.url_for("admin_serve_create_vessel_form"),
                status_code=f_status.HTTP_303_SEE_OTHER,
            )
        except Exception as e:
            request.session["flash_error"] = f"Nieoczekiwany błąd: {str(e)}"
            return RedirectResponse(
                request.url_for("admin_serve_vessels_list"),
                status_code=f_status.HTTP_303_SEE_OTHER,
            )


@router.get(
    "/{vessel_id}/edit",
    response_class=HTMLResponse,
    name="admin_serve_edit_vessel_form",
)
async def serve_edit_vessel_form_admin(request: Request, vessel_id: int):
    async with httpx.AsyncClient() as client:
        dropdown_data = await get_dropdown_data(client)
        vessel_data = request.session.pop(f"form_data_edit_{vessel_id}", None)
        api_error_form = request.session.pop(f"form_error_edit_{vessel_id}", None)

        if (
            not vessel_data
        ):  # Jeśli nie ma danych z sesji (np. po błędzie), pobierz z API
            try:
                response = await client.get(
                    f"{VESSEL_API_BASE_URL}/vessels/{vessel_id}"
                )
                response.raise_for_status()
                vessel_data = response.json()
            except Exception as e:
                request.session["flash_error"] = (
                    f"Nie można załadować danych statku (ID: {vessel_id}) do edycji: {str(e)}"
                )
                return RedirectResponse(
                    request.url_for("admin_serve_vessels_list"),
                    status_code=f_status.HTTP_303_SEE_OTHER,
                )

    current_year = datetime.now().year
    return templates.TemplateResponse(
        "admin/vessels_form.html",
        {
            "request": request,
            "form_title": f"Edytuj Statek: {vessel_data.get('name', '')}",
            "form_action_url": request.url_for(
                "admin_handle_edit_vessel_proxy", vessel_id=vessel_id
            ),
            "submit_button_text": "Zapisz Zmiany",
            "vessel": vessel_data,
            "vessel_types": dropdown_data["vessel_types"],
            "operators": dropdown_data["operators"],
            "fleets": dropdown_data["fleets"],
            "api_error": api_error_form,
            "current_year": current_year,
            "edit_mode": True,
        },
    )


@router.post("/{vessel_id}/edit", name="admin_handle_edit_vessel_proxy")
async def handle_edit_vessel_proxy_admin(
    request: Request,
    vessel_id: int,
    name: str = Form(...),
    vessel_type_id: int = Form(...),
    operator_id: int = Form(...),
    fleet_id: Optional[int] = Form(None),
    production_year: Optional[int] = Form(None),
    registration_number: Optional[str] = Form(None),
    imo_number: Optional[str] = Form(None),
    mmsi_number: Optional[str] = Form(None),
    call_sign: Optional[str] = Form(None),
    status: str = Form("active"),
):
    api_data = {
        "name": name,
        "vessel_type_id": vessel_type_id,
        "operator_id": operator_id,
        "fleet_id": fleet_id,
        "production_year": production_year,
        "registration_number": registration_number,
        "imo_number": imo_number,
        "mmsi_number": mmsi_number,
        "call_sign": call_sign,
        "status": status,
    }
    api_data_cleaned = {
        k: v for k, v in api_data.items() if v is not None or k in ["fleet_id"]
    }  # fleet_id może być None

    async with httpx.AsyncClient() as client:
        try:
            response = await client.put(
                f"{VESSEL_API_BASE_URL}/vessels/{vessel_id}", json=api_data_cleaned
            )
            response.raise_for_status()
            request.session["flash_success"] = (
                f"Dane statku (ID: {vessel_id}) zostały pomyślnie zaktualizowane."
            )
            return RedirectResponse(
                request.url_for("admin_serve_vessels_list"),
                status_code=f_status.HTTP_303_SEE_OTHER,
            )
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json().get("detail", str(e.response.content))
            except json.JSONDecodeError:
                detail = str(e.response.content)
            request.session[f"form_error_edit_{vessel_id}"] = (
                f"Błąd API ({e.response.status_code}): {detail}"
            )
            # Zapisz dane z formularza do sesji, aby ponownie wypełnić formularz
            request.session[f"form_data_edit_{vessel_id}"] = (
                api_data  # Użyj oryginalnych danych z formularza
            )
            return RedirectResponse(
                request.url_for("admin_serve_edit_vessel_form", vessel_id=vessel_id),
                status_code=f_status.HTTP_303_SEE_OTHER,
            )
        except Exception as e:
            request.session["flash_error"] = f"Nieoczekiwany błąd: {str(e)}"
            return RedirectResponse(
                request.url_for("admin_serve_vessels_list"),
                status_code=f_status.HTTP_303_SEE_OTHER,
            )


@router.post("/{vessel_id}/delete", name="admin_handle_delete_vessel_proxy")
async def handle_delete_vessel_proxy_admin(request: Request, vessel_id: int):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(f"{VESSEL_API_BASE_URL}/vessels/{vessel_id}")
            response.raise_for_status()  # Rzuci błąd dla 4xx/5xx, w tym 404, 409
            request.session["flash_success"] = (
                f"Statek (ID: {vessel_id}) został pomyślnie usunięty."
            )
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json().get("detail", str(e.response.content))
            except json.JSONDecodeError:
                detail = str(e.response.content)
            request.session["flash_error"] = (
                f"Błąd usuwania statku (status: {e.response.status_code}): {detail}"
            )
        except Exception as e:
            request.session["flash_error"] = (
                f"Nieoczekiwany błąd podczas usuwania statku: {str(e)}"
            )
    return RedirectResponse(
        request.url_for("admin_serve_vessels_list"),
        status_code=f_status.HTTP_303_SEE_OTHER,
    )
