from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
import httpx
import os
import json
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

from pa_app.routers.login import get_current_active_user
from pa_app.utils.utils import templates

VESSEL_API_BASE_URL = os.getenv("VESSEL_API_URL")

router = APIRouter(
    prefix="/admin/vessel-types",
    tags=["Admin - Vessel Types Management"],
    dependencies=[Depends(get_current_active_user)],
)


# --- Helper do pobierania listy producentów dla dropdownu ---
async def get_manufacturers_for_dropdown(client: httpx.AsyncClient) -> List[dict]:
    try:
        response = await client.get(
            f"{VESSEL_API_BASE_URL}/manufacturers/?limit=1000"
        )  # Pobierz wszystkich
        response.raise_for_status()
        return response.json()
    except Exception:
        return []


# --- Helper do pobierania listy klas czujników dla dropdownu ---
async def get_sensor_classes_for_dropdown(client: httpx.AsyncClient) -> List[dict]:
    try:
        # Użyj poprawnej ścieżki do endpointu zwracającego wszystkie klasy czujników
        response = await client.get(
            f"{VESSEL_API_BASE_URL}/sensor-classes/?limit=1000"
        )  # Zakładając, że masz taki endpoint
        # Lub jeśli użyłeś ścieżki z poprzedniej sugestii:
        # response = await client.get(f"{VESSEL_API_BASE_URL}/vessel-types/available-sensor-classes/")
        response.raise_for_status()
        return response.json()
    except Exception:
        return []


# --- Endpointy dla VesselType ---


@router.get("/", response_class=HTMLResponse, name="admin_serve_vessel_types_list")
async def serve_vessel_types_list_admin(request: Request):
    vessel_types_list = []
    api_error_load = None
    success_message = request.session.pop("flash_success", None)
    error_message = request.session.pop("flash_error", None)
    current_year = datetime.now().year

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{VESSEL_API_BASE_URL}/vessel-types/")
            response.raise_for_status()
            vessel_types_list = response.json()
        except httpx.HTTPStatusError as e:
            detail = (
                e.response.json().get("detail", e.response.text)
                if e.response
                else str(e)
            )
            api_error_load = f"Błąd API podczas ładowania listy typów statków ({e.response.status_code if e.response else 'N/A'}): {detail}"
        except Exception as e:
            api_error_load = (
                f"Nieoczekiwany błąd podczas ładowania listy typów statków: {str(e)}"
            )

    return templates.TemplateResponse(
        "admin/vessel_types_list.html",
        {
            "request": request,
            "vessel_types_list": vessel_types_list,
            "api_error_load": api_error_load,
            "success_message": success_message,
            "error_message": error_message,
            "current_year": current_year,
        },
    )


@router.get(
    "/new", response_class=HTMLResponse, name="admin_serve_create_vessel_type_form"
)
async def serve_create_vessel_type_form_admin(request: Request):
    current_year = datetime.now().year
    form_error = request.session.pop("form_error", None)
    form_data = request.session.pop("form_data", {})
    manufacturers = []
    async with httpx.AsyncClient() as client:
        manufacturers = await get_manufacturers_for_dropdown(client)

    return templates.TemplateResponse(
        "admin/vessel_types_form.html",
        {
            "request": request,
            "form_title": "Dodaj Nowy Typ Statku",
            "form_action_url": request.url_for("admin_handle_create_vessel_type_proxy"),
            "submit_button_text": "Dodaj Typ Statku",
            "vessel_type": form_data or {},
            "manufacturers": manufacturers,
            "api_error": form_error,
            "current_year": current_year,
        },
    )


@router.post("/new", name="admin_handle_create_vessel_type_proxy")
async def handle_create_vessel_type_proxy_admin(
    request: Request,
    name: str = Form(...),
    manufacturer_id: int = Form(...),
    description: Optional[str] = Form(None),
    length_meters: Optional[Decimal] = Form(None),
    width_meters: Optional[Decimal] = Form(None),
    draft_meters: Optional[Decimal] = Form(None),
    max_speed_knots: Optional[Decimal] = Form(None),
):
    api_data = {
        "name": name,
        "manufacturer_id": manufacturer_id,
        "description": description,
        "length_meters": str(length_meters) if length_meters is not None else None,
        "width_meters": str(width_meters) if width_meters is not None else None,
        "draft_meters": str(draft_meters) if draft_meters is not None else None,
        "max_speed_knots": str(max_speed_knots)
        if max_speed_knots is not None
        else None,
    }
    # Usuń klucze z None, aby Pydantic w API backendu użył swoich wartości domyślnych, jeśli są
    api_data_cleaned = {k: v for k, v in api_data.items() if v is not None}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{VESSEL_API_BASE_URL}/vessel-types/", json=api_data_cleaned
            )
            response.raise_for_status()
            request.session["flash_success"] = "Typ statku został pomyślnie dodany."
        except httpx.HTTPStatusError as e:
            detail = (
                e.response.json().get("detail", e.response.text)
                if e.response
                else str(e)
            )
            if e.response and e.response.status_code == 422:  # Błąd walidacji Pydantic
                request.session["form_error"] = f"Błąd walidacji danych z API: {detail}"
                request.session["form_data"] = (
                    api_data  # Przekaż oryginalne dane do ponownego wypełnienia
                )
                return RedirectResponse(
                    request.url_for("admin_serve_create_vessel_type_form"),
                    status_code=status.HTTP_303_SEE_OTHER,
                )
            request.session["flash_error"] = (
                f"Błąd API ({e.response.status_code if e.response else 'N/A'}): {detail}"
            )
        except Exception as e:
            request.session["flash_error"] = f"Nieoczekiwany błąd: {str(e)}"

    return RedirectResponse(
        request.url_for("admin_serve_vessel_types_list"),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get(
    "/{vessel_type_id}/edit",
    response_class=HTMLResponse,
    name="admin_serve_edit_vessel_type_form",
)
async def serve_edit_vessel_type_form_admin(request: Request, vessel_type_id: int):
    vessel_type_data = request.session.pop(f"form_data_edit_{vessel_type_id}", None)
    api_error_form = request.session.pop(f"form_error_edit_{vessel_type_id}", None)
    current_year = datetime.now().year
    manufacturers = []

    async with httpx.AsyncClient() as client:
        manufacturers = await get_manufacturers_for_dropdown(client)
        if (
            not vessel_type_data
        ):  # Jeśli nie ma danych z sesji (np. po błędzie walidacji)
            try:
                response = await client.get(
                    f"{VESSEL_API_BASE_URL}/vessel-types/{vessel_type_id}"
                )
                response.raise_for_status()
                vessel_type_data = response.json()
            except httpx.HTTPStatusError as e:
                detail = (
                    e.response.json().get("detail", e.response.text)
                    if e.response
                    else str(e)
                )
                request.session["flash_error"] = (
                    f"Nie można załadować typu statku (ID: {vessel_type_id}). Błąd API ({e.response.status_code if e.response else 'N/A'}): {detail}"
                )
                return RedirectResponse(
                    request.url_for("admin_serve_vessel_types_list"),
                    status_code=status.HTTP_303_SEE_OTHER,
                )
            except Exception as e:
                request.session["flash_error"] = (
                    f"Nieoczekiwany błąd podczas ładowania typu statku (ID: {vessel_type_id}): {str(e)}"
                )
                return RedirectResponse(
                    request.url_for("admin_serve_vessel_types_list"),
                    status_code=status.HTTP_303_SEE_OTHER,
                )

    return templates.TemplateResponse(
        "admin/vessel_types_form.html",
        {
            "request": request,
            "form_title": f"Edytuj Typ Statku: {vessel_type_data.get('name', '')}",
            "form_action_url": request.url_for(
                "admin_handle_edit_vessel_type_proxy", vessel_type_id=vessel_type_id
            ),
            "submit_button_text": "Zapisz Zmiany",
            "vessel_type": vessel_type_data,
            "manufacturers": manufacturers,
            "api_error": api_error_form,
            "current_year": current_year,
        },
    )


@router.post("/{vessel_type_id}/edit", name="admin_handle_edit_vessel_type_proxy")
async def handle_edit_vessel_type_proxy_admin(
    request: Request,
    vessel_type_id: int,
    name: str = Form(...),
    manufacturer_id: int = Form(...),
    description: Optional[str] = Form(None),
    length_meters: Optional[Decimal] = Form(None),
    width_meters: Optional[Decimal] = Form(None),
    draft_meters: Optional[Decimal] = Form(None),
    max_speed_knots: Optional[Decimal] = Form(None),
):
    api_data = {
        "name": name,
        "manufacturer_id": manufacturer_id,
        "description": description,
        "length_meters": str(length_meters) if length_meters is not None else None,
        "width_meters": str(width_meters) if width_meters is not None else None,
        "draft_meters": str(draft_meters) if draft_meters is not None else None,
        "max_speed_knots": str(max_speed_knots)
        if max_speed_knots is not None
        else None,
    }
    api_data_cleaned = {k: v for k, v in api_data.items() if v is not None}
    form_data_for_retry = {"id": vessel_type_id, **api_data}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.put(
                f"{VESSEL_API_BASE_URL}/vessel-types/{vessel_type_id}",
                json=api_data_cleaned,
            )
            response.raise_for_status()
            request.session["flash_success"] = (
                f"Dane typu statku (ID: {vessel_type_id}) zostały pomyślnie zaktualizowane."
            )
        except httpx.HTTPStatusError as e:
            detail = (
                e.response.json().get("detail", e.response.text)
                if e.response
                else str(e)
            )
            if e.response and e.response.status_code == 422:
                request.session[f"form_error_edit_{vessel_type_id}"] = (
                    f"Błąd walidacji danych z API: {detail}"
                )
                request.session[f"form_data_edit_{vessel_type_id}"] = (
                    form_data_for_retry
                )
                return RedirectResponse(
                    request.url_for(
                        "admin_serve_edit_vessel_type_form",
                        vessel_type_id=vessel_type_id,
                    ),
                    status_code=status.HTTP_303_SEE_OTHER,
                )
            request.session["flash_error"] = (
                f"Błąd API ({e.response.status_code if e.response else 'N/A'}): {detail}"
            )
        except Exception as e:
            request.session["flash_error"] = f"Nieoczekiwany błąd: {str(e)}"

    return RedirectResponse(
        request.url_for("admin_serve_vessel_types_list"),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/{vessel_type_id}/delete", name="admin_handle_delete_vessel_type_proxy")
async def handle_delete_vessel_type_proxy_admin(request: Request, vessel_type_id: int):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(
                f"{VESSEL_API_BASE_URL}/vessel-types/{vessel_type_id}"
            )
            if response.status_code == status.HTTP_204_NO_CONTENT:
                request.session["flash_success"] = (
                    f"Typ statku (ID: {vessel_type_id}) został pomyślnie usunięty."
                )
            else:
                response.raise_for_status()
        except httpx.HTTPStatusError as e:
            detail = f"Błąd serwera API (status: {e.response.status_code})."
            try:
                # Spróbuj sparsować JSON, jeśli jest dostępny
                error_content = e.response.json()
                detail = error_content.get(
                    "detail", str(error_content)
                )  # Użyj detail lub całego JSONa jako string
            except json.JSONDecodeError:
                # Jeśli odpowiedź nie jest JSONem, użyj surowego tekstu odpowiedzi
                if e.response.text:
                    detail = e.response.text
            print(
                f"PROXY API Error on DELETE /vessel-types/{vessel_type_id}: Status {e.response.status_code}, Detail: {detail}"
            )
            request.session["flash_error"] = (
                f"Błąd usuwania typu statku (status: {e.response.status_code}): {detail[:200]}"  # Ogranicz długość komunikatu
            )
        except Exception as e:
            request.session["flash_error"] = (
                f"Nieoczekiwany błąd podczas usuwania typu statku: {str(e)}"
            )
    return RedirectResponse(
        request.url_for("admin_serve_vessel_types_list"),
        status_code=status.HTTP_303_SEE_OTHER,
    )


# --- Endpointy dla zarządzania wymaganiami czujników dla VesselType ---


@router.get(
    "/{vessel_type_id}/sensor-requirements",
    response_class=HTMLResponse,
    name="admin_serve_sensor_requirements",
)
async def serve_sensor_requirements_page(request: Request, vessel_type_id: int):
    vessel_type_data = None
    current_requirements = []
    available_sensor_classes = []
    page_error = None  # Ogólny błąd ładowania strony
    current_year = datetime.now().year

    async with httpx.AsyncClient() as client:
        try:
            # 1. Pobierz dane VesselType
            vt_response = await client.get(
                f"{VESSEL_API_BASE_URL}/vessel-types/{vessel_type_id}"
            )
            if vt_response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"Vessel Type with ID {vessel_type_id} not found in API.",
                )
            vt_response.raise_for_status()  # Rzuci błąd dla innych statusów 4xx/5xx
            vessel_type_data = vt_response.json()

            # 2. Pobierz aktualne wymagania czujników dla tego VesselType
            req_response = await client.get(
                f"{VESSEL_API_BASE_URL}/vessel-types/{vessel_type_id}/sensor-requirements"
            )
            # Nawet jeśli nie ma wymagań, API powinno zwrócić 200 OK z pustą listą
            if (
                req_response.status_code == 404
            ):  # To nie powinno się zdarzyć, jeśli VesselType istnieje
                print(
                    f"Warning: Sensor requirements endpoint returned 404 for existing vessel type {vessel_type_id}"
                )
            else:
                req_response.raise_for_status()
                current_requirements = req_response.json()

            # 3. Pobierz listę wszystkich dostępnych SensorClass
            sc_response = await client.get(
                f"{VESSEL_API_BASE_URL}/sensor-classes/?limit=1000"
            )  # Użyj nowego prefixu
            sc_response.raise_for_status()
            available_sensor_classes = sc_response.json()

        except HTTPException as e:  # Przechwyć HTTPException rzucony przez nas
            page_error = e.detail
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json().get("detail", e.response.text)
            except json.JSONDecodeError:
                detail = e.response.text
            page_error = f"Błąd API ({e.response.status_code}) podczas ładowania danych: {detail}"
            print(f"API Error (sensor req page): {page_error}")
        except Exception as e:
            page_error = f"Nieoczekiwany błąd podczas ładowania danych: {str(e)}"
            print(f"Unexpected Error (sensor req page): {page_error}")

    if (
        not vessel_type_data and not page_error
    ):  # Jeśli nie było błędu, a vessel_type_data nadal None
        page_error = f"Nie znaleziono typu statku o ID {vessel_type_id}."

    # Komunikaty flash z sesji (jeśli są używane dla akcji na tej stronie)
    success_message = request.session.pop(f"flash_success_vt_{vessel_type_id}_sr", None)
    error_message = request.session.pop(f"flash_error_vt_{vessel_type_id}_sr", None)

    return templates.TemplateResponse(
        "admin/vessel_type_sensor_requirements.html",  # Upewnij się, że nazwa pliku jest poprawna
        {
            "request": request,
            "vessel_type": vessel_type_data,
            "requirements": current_requirements,
            "available_sensor_classes": available_sensor_classes,
            "page_error": page_error,  # Błąd ładowania danych strony
            "success_message": success_message,  # Flash message
            "error_message": error_message,  # Flash message
            "current_year": current_year,
        },
    )


@router.post(
    "/{vessel_type_id}/sensor-requirements", name="admin_handle_add_sensor_requirement"
)
async def handle_add_sensor_requirement_proxy(
    request: Request,
    vessel_type_id: int,
    sensor_class_id: int = Form(...),
    quantity: int = Form(1),
    required: Optional[bool] = Form(
        False
    ),  # Checkbox zwróci wartość tylko jeśli zaznaczony
):
    api_data = {
        "sensor_class_id": sensor_class_id,
        "quantity": quantity,
        "required": True if required else False,  # Konwersja z wartości checkboxa
    }
    redirect_url = request.url_for(
        "admin_serve_sensor_requirements", vessel_type_id=vessel_type_id
    )

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{VESSEL_API_BASE_URL}/vessel-types/{vessel_type_id}/sensor-requirements",
                json=api_data,
            )
            response.raise_for_status()
            request.session[f"flash_success_vt_{vessel_type_id}_sr"] = (
                "Wymaganie czujnika zostało pomyślnie dodane."
            )
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json().get("detail", e.response.text)
            except json.JSONDecodeError:
                detail = e.response.text
            request.session[f"flash_error_vt_{vessel_type_id}_sr"] = (
                f"Błąd API przy dodawaniu ({e.response.status_code}): {detail}"
            )
        except Exception as e:
            request.session[f"flash_error_vt_{vessel_type_id}_sr"] = (
                f"Nieoczekiwany błąd przy dodawaniu: {str(e)}"
            )

    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)


@router.post(
    "/{vessel_type_id}/sensor-requirements/{sensor_class_id}/update",
    name="admin_handle_update_sensor_requirement",
)
async def handle_update_sensor_requirement_proxy(
    request: Request,
    vessel_type_id: int,
    sensor_class_id: int,
    quantity: int = Form(...),
    required: Optional[bool] = Form(False),
):
    api_data = {"quantity": quantity, "required": True if required else False}
    # Usuń klucze, jeśli nie zostały przekazane (jeśli schemat API Update ma pola opcjonalne)
    # Na razie zakładamy, że zawsze aktualizujemy oba.

    redirect_url = request.url_for(
        "admin_serve_sensor_requirements", vessel_type_id=vessel_type_id
    )

    async with httpx.AsyncClient() as client:
        try:
            response = await client.put(
                f"{VESSEL_API_BASE_URL}/vessel-types/{vessel_type_id}/sensor-requirements/{sensor_class_id}",
                json=api_data,
            )
            response.raise_for_status()
            request.session[f"flash_success_vt_{vessel_type_id}_sr"] = (
                "Wymaganie czujnika zostało zaktualizowane."
            )
        except httpx.HTTPStatusError as e:
            # ... (obsługa błędów jak w add) ...
            try:
                detail = e.response.json().get("detail", e.response.text)
            except json.JSONDecodeError:
                detail = e.response.text
            request.session[f"flash_error_vt_{vessel_type_id}_sr"] = (
                f"Błąd API przy aktualizacji ({e.response.status_code}): {detail}"
            )
        except Exception as e:
            request.session[f"flash_error_vt_{vessel_type_id}_sr"] = (
                f"Nieoczekiwany błąd przy aktualizacji: {str(e)}"
            )

    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)


@router.post(
    "/{vessel_type_id}/sensor-requirements/{sensor_class_id}/delete",
    name="admin_handle_remove_sensor_requirement",
)
async def handle_remove_sensor_requirement_proxy(
    request: Request, vessel_type_id: int, sensor_class_id: int
):
    redirect_url = request.url_for(
        "admin_serve_sensor_requirements", vessel_type_id=vessel_type_id
    )
    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(
                f"{VESSEL_API_BASE_URL}/vessel-types/{vessel_type_id}/sensor-requirements/{sensor_class_id}"
            )
            response.raise_for_status()  # Oczekujemy 204 No Content
            request.session[f"flash_success_vt_{vessel_type_id}_sr"] = (
                "Wymaganie czujnika zostało usunięte."
            )
        except httpx.HTTPStatusError as e:
            # ... (obsługa błędów jak w add) ...
            try:
                detail = e.response.json().get("detail", e.response.text)
            except json.JSONDecodeError:
                detail = e.response.text
            request.session[f"flash_error_vt_{vessel_type_id}_sr"] = (
                f"Błąd API przy usuwaniu ({e.response.status_code}): {detail}"
            )
        except Exception as e:
            request.session[f"flash_error_vt_{vessel_type_id}_sr"] = (
                f"Nieoczekiwany błąd przy usuwaniu: {str(e)}"
            )

    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
