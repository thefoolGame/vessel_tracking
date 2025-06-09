from fastapi import APIRouter, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import httpx
import os
import json
from datetime import date
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple, Sequence, Union

from pa_app.routers.login import get_current_active_user
from pa_app.utils.utils import templates

PrimitiveType = Union[str, int, float, bool, None]

VESSEL_API_BASE_URL = os.getenv("VESSEL_API_URL")

router = APIRouter(
    prefix="/admin/vessels/{vessel_id}/sensors",
    tags=["Admin - Vessel Sensors Management"],
    dependencies=[Depends(get_current_active_user)],
)


# Funkcja pomocnicza do pobierania szczegółów statku
async def fetch_vessel_details(
    client: httpx.AsyncClient, vessel_id: int
) -> Optional[Dict[str, Any]]:
    try:
        response = await client.get(f"{VESSEL_API_BASE_URL}/vessels/{vessel_id}")
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


# Funkcja pomocnicza do pobierania statusu konfiguracji czujników
async def fetch_sensor_configuration_status(
    client: httpx.AsyncClient, vessel_id: int
) -> Optional[Dict[str, Any]]:
    try:
        response = await client.get(
            f"{VESSEL_API_BASE_URL}/vessels/{vessel_id}/sensor-configuration-status"
        )
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


# Funkcja pomocnicza do pobierania zainstalowanych czujników
async def fetch_installed_sensors(
    client: httpx.AsyncClient, vessel_id: int
) -> List[Dict[str, Any]]:
    try:
        response = await client.get(
            f"{VESSEL_API_BASE_URL}/vessels/{vessel_id}/sensors/?limit=1000"  # Pobierz wszystkie
        )
        response.raise_for_status()
        return response.json()
    except Exception:
        return []


# Funkcja pomocnicza do pobierania typów czujników (SensorType) na podstawie listy ID klas
async def fetch_allowed_sensor_types(
    client: httpx.AsyncClient, sensor_class_ids: List[int]
) -> List[Dict[str, Any]]:
    if not sensor_class_ids:
        return []
    try:
        params: List[Tuple[str, PrimitiveType]] = [
            ("sensor_class_ids", str(id)) for id in sensor_class_ids
        ]

        response = await client.get(
            f"{VESSEL_API_BASE_URL}/sensor-types/?limit=1000",  # Pobierz wszystkie pasujące
            params=params,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching allowed sensor types: {e}")  # Logowanie błędu
        return []


@router.get(
    "/",  # Ścieżka będzie /admin/vessels/{vessel_id}/sensors/
    response_class=HTMLResponse,
    name="admin_serve_vessel_sensors_management",
)
async def serve_vessel_sensors_management_page(
    request: Request,
    vessel_id: int,  # Pobierane z parametru ścieżki zdefiniowanego przy include_router
):
    async with httpx.AsyncClient() as client:
        vessel_details = await fetch_vessel_details(client, vessel_id)
        if not vessel_details:
            # [propozycja] Ustawienie komunikatu flash i przekierowanie na listę statków
            request.session["flash_error"] = f"Nie znaleziono statku o ID: {vessel_id}."
            return RedirectResponse(
                request.url_for(
                    "admin_serve_vessels_list"
                ),  # Zakładając, że masz taki route name
                status_code=status.HTTP_303_SEE_OTHER,
            )

        sensor_config_status = await fetch_sensor_configuration_status(
            client, vessel_id
        )
        installed_sensors = await fetch_installed_sensors(client, vessel_id)

        # Pobierz ID dozwolonych klas czujników, aby pobrać odpowiednie typy SensorType
        allowed_sensor_class_ids = []
        if sensor_config_status and sensor_config_status.get("allowed_classes"):
            allowed_sensor_class_ids = [
                cls.get("sensor_class_id")
                for cls in sensor_config_status["allowed_classes"]
                if cls.get("sensor_class_id") is not None
            ]

        # Pobierz listę SensorType, które mogą być użyte do dodania nowego sensora
        available_sensor_types_for_form = await fetch_allowed_sensor_types(
            client, allowed_sensor_class_ids
        )

    success_message = request.session.pop("flash_success", None)
    error_message = request.session.pop("flash_error", None)
    form_error = request.session.pop("sensor_form_error", None)
    form_data = request.session.pop("sensor_form_data", {})

    return templates.TemplateResponse(
        "admin/vessel_sensors_management.html",
        {
            "request": request,
            "vessel": vessel_details,
            "sensor_config_status": sensor_config_status,
            "installed_sensors": installed_sensors,
            "available_sensor_types": available_sensor_types_for_form,  # Dla dropdownu w formularzu
            "success_message": success_message,
            "error_message": error_message,
            "form_error": form_error,  # Błędy specyficzne dla formularza dodawania/edycji sensora
            "form_data": form_data,  # Dane do ponownego wypełnienia formularza sensora
            "page_title": f"Zarządzanie Czujnikami dla Statku: {vessel_details.get('name', '')}",
        },
    )


@router.post(
    "/",  # Akcja dla tworzenia nowego sensora
    name="admin_handle_create_vessel_sensor",
    response_class=RedirectResponse,
)
async def handle_create_vessel_sensor_proxy(
    request: Request,
    vessel_id: int,
    name: str = Form(...),
    sensor_type_id: int = Form(...),
    serial_number: Optional[str] = Form(None),
    installation_date: Optional[date] = Form(None),
    callibration_date: Optional[date] = Form(None),
    location_on_boat: Optional[str] = Form(None),
    measurement_unit: Optional[str] = Form(None),
    min_val: Optional[Decimal] = Form(None),
    max_val: Optional[Decimal] = Form(None),
):
    api_data = {
        "name": name,
        "sensor_type_id": sensor_type_id,
        "serial_number": serial_number,
        "installation_date": installation_date.isoformat()
        if installation_date
        else None,
        "callibration_date": callibration_date.isoformat()
        if callibration_date
        else None,
        "location_on_boat": location_on_boat,
        "measurement_unit": measurement_unit,
        "min_val": str(min_val) if min_val is not None else None,
        "max_val": str(max_val) if max_val is not None else None,
    }
    api_data_cleaned = {k: v for k, v in api_data.items() if v is not None}

    redirect_url = request.url_for(
        "admin_serve_vessel_sensors_management", vessel_id=vessel_id
    )

    async with httpx.AsyncClient() as client:
        try:
            # Endpoint API backendu to /vessels/{vessel_id}/sensors/
            response = await client.post(
                f"{VESSEL_API_BASE_URL}/vessels/{vessel_id}/sensors/",
                json=api_data_cleaned,
            )
            response.raise_for_status()
            request.session["flash_success"] = "Nowy czujnik został pomyślnie dodany."
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json().get("detail", str(e.response.content))
            except json.JSONDecodeError:
                detail = e.response.text
            request.session[f"sensor_form_error_{vessel_id}"] = (
                f"Błąd API ({e.response.status_code}): {detail}"
            )
            # Zapisz dane z formularza do sesji, aby ponownie wypełnić formularz
            # Przekazujemy oryginalne typy, niekoniecznie te po konwersji do string
            form_data_for_retry = {
                k: Form(...) for k, v_ in locals().items() if k in api_data_cleaned
            }
            form_data_for_retry.update(
                {
                    "name": name,
                    "sensor_type_id": sensor_type_id,
                    "serial_number": serial_number,
                    "installation_date": installation_date,
                    "callibration_date": callibration_date,
                    "location_on_boat": location_on_boat,
                    "measurement_unit": measurement_unit,
                    "min_val": min_val,
                    "max_val": max_val,
                }
            )
            request.session[f"sensor_form_data_{vessel_id}"] = form_data_for_retry
        except Exception as e:
            request.session["flash_error"] = (
                f"Nieoczekiwany błąd podczas dodawania czujnika: {str(e)}"
            )

    return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)


@router.post(
    "/{sensor_id}",  # Akcja dla edycji istniejącego sensora
    name="admin_handle_edit_vessel_sensor",  # Nazwa dla faktycznej akcji formularza
    response_class=RedirectResponse,
)
async def handle_edit_vessel_sensor_proxy(
    request: Request,
    vessel_id: int,
    sensor_id: int,  # ID edytowanego sensora
    name: str = Form(...),
    sensor_type_id: int = Form(...),
    serial_number: Optional[str] = Form(None),
    installation_date: Optional[date] = Form(None),
    callibration_date: Optional[date] = Form(None),
    location_on_boat: Optional[str] = Form(None),
    measurement_unit: Optional[str] = Form(None),
    min_val: Optional[Decimal] = Form(None),
    max_val: Optional[Decimal] = Form(None),
):
    api_data = {
        "name": name,
        "sensor_type_id": sensor_type_id,
        "serial_number": serial_number,
        "installation_date": installation_date.isoformat()
        if installation_date
        else None,
        "callibration_date": callibration_date.isoformat()
        if callibration_date
        else None,
        "location_on_boat": location_on_boat,
        "measurement_unit": measurement_unit,
        "min_val": str(min_val) if min_val is not None else None,
        "max_val": str(max_val) if max_val is not None else None,
    }
    api_data_cleaned = {k: v for k, v in api_data.items() if v is not None}

    redirect_url = request.url_for(
        "admin_serve_vessel_sensors_management", vessel_id=vessel_id
    )

    async with httpx.AsyncClient() as client:
        try:
            # Endpoint API backendu to /vessels/{vessel_id}/sensors/{sensor_id}
            response = await client.put(
                f"{VESSEL_API_BASE_URL}/vessels/{vessel_id}/sensors/{sensor_id}",
                json=api_data_cleaned,
            )
            response.raise_for_status()
            request.session["flash_success"] = (
                f"Czujnik (ID: {sensor_id}) został pomyślnie zaktualizowany."
            )
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json().get("detail", str(e.response.content))
            except json.JSONDecodeError:
                detail = e.response.text
            request.session[f"sensor_form_error_{vessel_id}"] = (
                f"Błąd API ({e.response.status_code}): {detail}"
            )
            form_data_for_retry = {
                k: Form(...) for k, v_ in locals().items() if k in api_data_cleaned
            }
            form_data_for_retry.update(
                {
                    "id": sensor_id,  # Dodaj ID edytowanego sensora
                    "name": name,
                    "sensor_type_id": sensor_type_id,
                    "serial_number": serial_number,
                    "installation_date": installation_date,
                    "callibration_date": callibration_date,
                    "location_on_boat": location_on_boat,
                    "measurement_unit": measurement_unit,
                    "min_val": min_val,
                    "max_val": max_val,
                }
            )
            request.session[f"sensor_form_data_{vessel_id}"] = form_data_for_retry
        except Exception as e:
            request.session["flash_error"] = (
                f"Nieoczekiwany błąd podczas aktualizacji czujnika: {str(e)}"
            )

    return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)


@router.post(
    "/{sensor_id}/delete",
    name="admin_handle_delete_vessel_sensor",
    response_class=RedirectResponse,
)
async def handle_delete_vessel_sensor_proxy(
    request: Request,
    vessel_id: int,
    sensor_id: int,
):
    redirect_url = request.url_for(
        "admin_serve_vessel_sensors_management", vessel_id=vessel_id
    )
    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(
                f"{VESSEL_API_BASE_URL}/vessels/{vessel_id}/sensors/{sensor_id}"
            )
            if response.status_code == status.HTTP_204_NO_CONTENT:
                request.session["flash_success"] = (
                    f"Czujnik (ID: {sensor_id}) został pomyślnie usunięty."
                )
            else:
                # Jeśli API zwraca inny status sukcesu lub błędu z ciałem
                response.raise_for_status()
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json().get("detail", str(e.response.content))
            except json.JSONDecodeError:
                detail = e.response.text
            request.session["flash_error"] = (
                f"Błąd usuwania czujnika (status: {e.response.status_code}): {detail}"
            )
        except Exception as e:
            request.session["flash_error"] = (
                f"Nieoczekiwany błąd podczas usuwania czujnika: {str(e)}"
            )

    return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
