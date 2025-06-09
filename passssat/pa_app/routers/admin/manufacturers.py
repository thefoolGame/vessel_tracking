from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse

# from starlette.datastructures import URL # Już niepotrzebne, jeśli nie budujemy URL z query params
import httpx
import os
import json
from typing import Optional
from datetime import datetime  # Potrzebne dla current_year

from pa_app.routers.login import get_current_active_user
from pa_app.utils.utils import templates

VESSEL_API_BASE_URL = os.getenv("VESSEL_API_URL")

router = APIRouter(
    prefix="/admin/manufacturers",
    tags=["Admin - Manufacturers Management"],
    dependencies=[Depends(get_current_active_user)],
)


# --- Endpoint GET listy - odczytuje komunikaty z sesji ---
@router.get("/", response_class=HTMLResponse, name="admin_serve_manufacturers_list")
async def serve_manufacturers_list_admin(request: Request):
    # Odczytaj i usuń flash messages z sesji
    success_message = request.session.pop("flash_success", None)
    error_message = request.session.pop("flash_error", None)

    manufacturers_list = []
    api_error_load = None  # Błąd specyficzny dla ładowania samej listy

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{VESSEL_API_BASE_URL}/manufacturers/")
            response.raise_for_status()
            manufacturers_list = response.json()
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json().get("detail", e.response.text)
            except json.JSONDecodeError:
                detail = e.response.text
            api_error_load = (
                f"Błąd API podczas ładowania listy ({e.response.status_code}): {detail}"
            )
            print(f"API Error (load list): {api_error_load}")
        except Exception as e:
            api_error_load = f"Nieoczekiwany błąd podczas ładowania listy: {str(e)}"
            print(f"Unexpected Error (load list): {api_error_load}")

    current_year = datetime.now().year
    return templates.TemplateResponse(
        "admin/manufacturers_list.html",  # Upewnij się, że nazwa pliku jest poprawna
        {
            "request": request,
            "manufacturers_list": manufacturers_list,
            "api_error_load": api_error_load,
            "success_message": success_message,  # Przekaż flash message do szablonu
            "error_message": error_message,  # Przekaż flash message do szablonu
            "current_year": current_year,
        },
    )


# --- Endpoint GET formularza tworzenia ---
@router.get(
    "/new", response_class=HTMLResponse, name="admin_serve_create_manufacturer_form"
)
async def serve_create_manufacturer_form_admin(request: Request):
    current_year = datetime.now().year
    # Odczytaj ewentualne błędy formularza przekazane przez flash (jeśli byśmy tak robili dla błędów walidacji)
    # Na razie błędy walidacji formularza są renderowane bezpośrednio
    form_error = request.session.pop("form_error", None)
    form_data = request.session.pop(
        "form_data", {}
    )  # Do ponownego wypełnienia formularza

    return templates.TemplateResponse(
        "admin/manufacturers_form.html",  # Upewnij się, że nazwa pliku jest poprawna
        {
            "request": request,
            "form_title": "Dodaj Nowego Producenta",
            "form_action_url": request.url_for(
                "admin_handle_create_manufacturer_proxy"
            ),
            "submit_button_text": "Dodaj Producenta",
            "manufacturer": form_data or {},  # Użyj danych z sesji lub pustego słownika
            "api_error": form_error,  # Błąd walidacji formularza z sesji
            "current_year": current_year,
        },
    )


# --- Endpoint POST tworzenia - używa sesji dla komunikatów ---
@router.post("/new", name="admin_handle_create_manufacturer_proxy")
async def handle_create_manufacturer_proxy_admin(
    request: Request,
    name: str = Form(...),
    country: Optional[str] = Form(None),
    website: Optional[str] = Form(None),
    contact_info: Optional[str] = Form(None),
):
    api_data = {"name": name, "country": country, "website": website}
    form_data_for_retry = {
        "name": name,
        "country": country,
        "website": website,
        "contact_info": contact_info,
    }

    if contact_info:
        try:
            api_data["contact_info"] = json.loads(contact_info)
        except json.JSONDecodeError:
            # Zapisz błąd i dane formularza do sesji, następnie przekieruj z powrotem do formularza GET
            request.session["form_error"] = (
                "Niepoprawny format JSON dla informacji kontaktowych."
            )
            request.session["form_data"] = form_data_for_retry
            return RedirectResponse(
                request.url_for("admin_serve_create_manufacturer_form"),
                status_code=status.HTTP_303_SEE_OTHER,
            )

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{VESSEL_API_BASE_URL}/manufacturers/", json=api_data
            )
            response.raise_for_status()
            request.session["flash_success"] = "Producent został pomyślnie dodany."
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json().get("detail", e.response.text)
            except json.JSONDecodeError:
                detail = e.response.text
            # Jeśli błąd walidacji z API (np. 422), zapisz błąd i dane do sesji, przekieruj do formularza
            if e.response.status_code == 422:
                request.session["form_error"] = f"Błąd walidacji danych z API: {detail}"
                request.session["form_data"] = form_data_for_retry
                return RedirectResponse(
                    request.url_for("admin_serve_create_manufacturer_form"),
                    status_code=status.HTTP_303_SEE_OTHER,
                )
            # Inne błędy API zapisz jako ogólny flash error
            request.session["flash_error"] = (
                f"Błąd API ({e.response.status_code}): {detail}"
            )
        except Exception as e:
            request.session["flash_error"] = f"Nieoczekiwany błąd: {str(e)}"

    return RedirectResponse(
        url=request.url_for("admin_serve_manufacturers_list"),  # Czysty URL
        status_code=status.HTTP_303_SEE_OTHER,
    )


# --- Endpoint GET formularza edycji - używa sesji dla komunikatów ---
@router.get(
    "/{manufacturer_id}/edit",
    response_class=HTMLResponse,
    name="admin_serve_edit_manufacturer_form",
)
async def serve_edit_manufacturer_form_admin(request: Request, manufacturer_id: int):
    manufacturer_data = request.session.pop(
        f"form_data_edit_{manufacturer_id}", None
    )  # Sprawdź, czy są dane z poprzedniego błędu
    api_error_form = request.session.pop(f"form_error_edit_{manufacturer_id}", None)
    current_year = datetime.now().year

    if not manufacturer_data:  # Jeśli nie ma danych z sesji, pobierz z API
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{VESSEL_API_BASE_URL}/manufacturers/{manufacturer_id}"
                )
                response.raise_for_status()
                manufacturer_data = response.json()
            except httpx.HTTPStatusError as e:
                try:
                    detail = e.response.json().get("detail", e.response.text)
                except json.JSONDecodeError:
                    detail = e.response.text
                request.session["flash_error"] = (
                    f"Nie można załadować producenta (ID: {manufacturer_id}) do edycji. Błąd API ({e.response.status_code}): {detail}"
                )
                return RedirectResponse(
                    request.url_for("admin_serve_manufacturers_list"),
                    status_code=status.HTTP_303_SEE_OTHER,
                )
            except Exception as e:
                request.session["flash_error"] = (
                    f"Wystąpił nieoczekiwany błąd podczas ładowania producenta (ID: {manufacturer_id}) do edycji: {str(e)}"
                )
                return RedirectResponse(
                    request.url_for("admin_serve_manufacturers_list"),
                    status_code=status.HTTP_303_SEE_OTHER,
                )

    contact_info_display = ""
    # Przygotuj contact_info_display na podstawie manufacturer_data (które może być z sesji lub API)
    raw_contact_info = manufacturer_data.get("contact_info")
    if isinstance(raw_contact_info, dict):  # Jeśli z API przyszło jako dict
        contact_info_display = json.dumps(
            raw_contact_info, indent=2, ensure_ascii=False
        )
    elif isinstance(
        raw_contact_info, str
    ):  # Jeśli z sesji (form_data) przyszło jako string
        contact_info_display = raw_contact_info

    return templates.TemplateResponse(
        "admin/manufacturers_form.html",
        {
            "request": request,
            "form_title": f"Edytuj Producenta: {manufacturer_data.get('name', '')}",
            "form_action_url": request.url_for(
                "admin_handle_edit_manufacturer_proxy", manufacturer_id=manufacturer_id
            ),
            "submit_button_text": "Zapisz Zmiany",
            "manufacturer": manufacturer_data,
            "contact_info_display": contact_info_display,
            "api_error": api_error_form,  # Błąd walidacji formularza z sesji
            "current_year": current_year,
        },
    )


# --- Endpoint POST edycji - używa sesji dla komunikatów ---
@router.post("/{manufacturer_id}/edit", name="admin_handle_edit_manufacturer_proxy")
async def handle_edit_manufacturer_proxy_admin(
    request: Request,
    manufacturer_id: int,
    name: str = Form(...),
    country: Optional[str] = Form(None),
    website: Optional[str] = Form(None),
    contact_info: Optional[str] = Form(None),
):
    api_data = {"name": name, "country": country, "website": website}
    form_data_for_retry = {
        "id": manufacturer_id,
        "name": name,
        "country": country,
        "website": website,
        "contact_info": contact_info,
    }

    if contact_info:
        try:
            api_data["contact_info"] = json.loads(contact_info)
        except json.JSONDecodeError:
            request.session[f"form_error_edit_{manufacturer_id}"] = (
                "Niepoprawny format JSON dla informacji kontaktowych."
            )
            request.session[f"form_data_edit_{manufacturer_id}"] = form_data_for_retry
            return RedirectResponse(
                request.url_for(
                    "admin_serve_edit_manufacturer_form",
                    manufacturer_id=manufacturer_id,
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

    async with httpx.AsyncClient() as client:
        try:
            response = await client.put(
                f"{VESSEL_API_BASE_URL}/manufacturers/{manufacturer_id}", json=api_data
            )
            response.raise_for_status()
            request.session["flash_success"] = (
                f"Dane producenta (ID: {manufacturer_id}) zostały pomyślnie zaktualizowane."
            )
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json().get("detail", e.response.text)
            except json.JSONDecodeError:
                detail = e.response.text
            if e.response.status_code == 422:  # Błąd walidacji Pydantic w API
                request.session[f"form_error_edit_{manufacturer_id}"] = (
                    f"Błąd walidacji danych z API: {detail}"
                )
                request.session[f"form_data_edit_{manufacturer_id}"] = (
                    form_data_for_retry
                )
                return RedirectResponse(
                    request.url_for(
                        "admin_serve_edit_manufacturer_form",
                        manufacturer_id=manufacturer_id,
                    ),
                    status_code=status.HTTP_303_SEE_OTHER,
                )
            request.session["flash_error"] = (
                f"Błąd API ({e.response.status_code}): {detail}"
            )
        except Exception as e:
            request.session["flash_error"] = f"Nieoczekiwany błąd: {str(e)}"

    return RedirectResponse(
        url=request.url_for("admin_serve_manufacturers_list"),  # Czysty URL
        status_code=status.HTTP_303_SEE_OTHER,
    )


# --- Endpoint POST usuwania - używa sesji dla komunikatów ---
@router.post("/{manufacturer_id}/delete", name="admin_handle_delete_manufacturer_proxy")
async def handle_delete_manufacturer_proxy_admin(
    request: Request, manufacturer_id: int
):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(
                f"{VESSEL_API_BASE_URL}/manufacturers/{manufacturer_id}"
            )
            if response.status_code == status.HTTP_204_NO_CONTENT:
                request.session["flash_success"] = (
                    f"Producent (ID: {manufacturer_id}) został pomyślnie usunięty."
                )
            else:
                response.raise_for_status()  # Rzuci błąd dla innych statusów niż 2xx
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json().get("detail", e.response.text)
            except json.JSONDecodeError:
                detail = e.response.text
            request.session["flash_error"] = (
                f"Błąd usuwania (status: {e.response.status_code}): {detail}"
            )
        except Exception as e:
            request.session["flash_error"] = (
                f"Nieoczekiwany błąd podczas usuwania: {str(e)}"
            )

    return RedirectResponse(
        url=request.url_for("admin_serve_manufacturers_list"),  # Czysty URL
        status_code=status.HTTP_303_SEE_OTHER,
    )
