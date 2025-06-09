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
    prefix="/admin/operators",  # Nowy prefix
    tags=["Admin - Operators Management"],
    dependencies=[Depends(get_current_active_user)],
)


# --- Endpoint GET listy operatorów ---
@router.get("/", response_class=HTMLResponse, name="admin_serve_operators_list")
async def serve_operators_list_admin(request: Request):
    success_message = request.session.pop("flash_success", None)
    error_message = request.session.pop("flash_error", None)
    operators_list = []
    api_error_load = None
    current_year = datetime.now().year

    async with httpx.AsyncClient() as client:
        try:
            # Użyj endpointu API, który zwraca operatorów z liczbami flot/statków
            response = await client.get(f"{VESSEL_API_BASE_URL}/operators/")
            response.raise_for_status()
            operators_list = response.json()
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json().get("detail", e.response.text)
            except json.JSONDecodeError:
                detail = e.response.text
            api_error_load = f"Błąd API podczas ładowania listy operatorów ({e.response.status_code}): {detail}"
        except Exception as e:
            api_error_load = (
                f"Nieoczekiwany błąd podczas ładowania listy operatorów: {str(e)}"
            )

    return templates.TemplateResponse(
        "admin/operators_list.html",
        {
            "request": request,
            "operators_list": operators_list,
            "api_error_load": api_error_load,
            "success_message": success_message,
            "error_message": error_message,
            "current_year": current_year,
        },
    )


# --- Endpoint GET formularza tworzenia operatora ---
@router.get(
    "/new", response_class=HTMLResponse, name="admin_serve_create_operator_form"
)
async def serve_create_operator_form_admin(request: Request):
    current_year = datetime.now().year
    form_error = request.session.pop("form_error_operator", None)
    form_data = request.session.pop("form_data_operator", {})

    return templates.TemplateResponse(
        "admin/operators_form.html",
        {
            "request": request,
            "form_title": "Dodaj Nowego Operatora",
            "form_action_url": request.url_for("admin_handle_create_operator_proxy"),
            "submit_button_text": "Dodaj Operatora",
            "operator": form_data or {},
            "api_error": form_error,
            "current_year": current_year,
        },
    )


# --- Endpoint POST tworzenia operatora ---
@router.post("/new", name="admin_handle_create_operator_proxy")
async def handle_create_operator_proxy_admin(
    request: Request,
    name: str = Form(...),
    contact_person: Optional[str] = Form(None),
    email: Optional[str] = Form(None),  # Na razie jako string, walidacja Pydantic w API
    phone: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
):
    api_data = {
        "name": name,
        "contact_person": contact_person,
        "email": email,
        "phone": phone,
        "address": address,
    }
    form_data_for_retry = api_data.copy()  # Kopiujemy do ponownego wypełnienia

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{VESSEL_API_BASE_URL}/operators/", json=api_data
            )
            response.raise_for_status()
            request.session["flash_success"] = "Operator został pomyślnie dodany."
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json().get("detail", e.response.text)
            except json.JSONDecodeError:
                detail = e.response.text
            if e.response.status_code == 422:  # Błąd walidacji Pydantic w API
                request.session["form_error_operator"] = (
                    f"Błąd walidacji danych z API: {detail}"
                )
                request.session["form_data_operator"] = form_data_for_retry
                return RedirectResponse(
                    request.url_for("admin_serve_create_operator_form"),
                    status_code=status.HTTP_303_SEE_OTHER,
                )
            request.session["flash_error"] = (
                f"Błąd API ({e.response.status_code}): {detail}"
            )
        except Exception as e:
            request.session["flash_error"] = f"Nieoczekiwany błąd: {str(e)}"

    return RedirectResponse(
        url=request.url_for("admin_serve_operators_list"),
        status_code=status.HTTP_303_SEE_OTHER,
    )


# --- Endpoint GET formularza edycji operatora ---
@router.get(
    "/{operator_id}/edit",
    response_class=HTMLResponse,
    name="admin_serve_edit_operator_form",
)
async def serve_edit_operator_form_admin(request: Request, operator_id: int):
    operator_data = request.session.pop(f"form_data_operator_edit_{operator_id}", None)
    api_error_form = request.session.pop(
        f"form_error_operator_edit_{operator_id}", None
    )
    current_year = datetime.now().year

    if (
        not operator_data
    ):  # Jeśli nie ma danych z sesji (np. po błędzie walidacji), pobierz z API
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{VESSEL_API_BASE_URL}/operators/{operator_id}"
                )
                response.raise_for_status()
                operator_data = response.json()
            except httpx.HTTPStatusError as e:
                try:
                    detail = e.response.json().get("detail", e.response.text)
                except json.JSONDecodeError:
                    detail = e.response.text
                request.session["flash_error"] = (
                    f"Nie można załadować operatora (ID: {operator_id}) do edycji. Błąd API ({e.response.status_code}): {detail}"
                )
                return RedirectResponse(
                    request.url_for("admin_serve_operators_list"),
                    status_code=status.HTTP_303_SEE_OTHER,
                )
            except Exception as e:
                request.session["flash_error"] = (
                    f"Wystąpił nieoczekiwany błąd podczas ładowania operatora (ID: {operator_id}) do edycji: {str(e)}"
                )
                return RedirectResponse(
                    request.url_for("admin_serve_operators_list"),
                    status_code=status.HTTP_303_SEE_OTHER,
                )

    if not operator_data:  # Dodatkowe zabezpieczenie, jeśli API nie zwróciło danych
        request.session["flash_error"] = (
            f"Nie znaleziono operatora o ID: {operator_id}."
        )
        return RedirectResponse(
            request.url_for("admin_serve_operators_list"),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return templates.TemplateResponse(
        "admin/operators_form.html",
        {
            "request": request,
            "form_title": f"Edytuj Operatora: {operator_data.get('name', '')}",
            "form_action_url": request.url_for(
                "admin_handle_edit_operator_proxy", operator_id=operator_id
            ),
            "submit_button_text": "Zapisz Zmiany",
            "operator": operator_data,
            "api_error": api_error_form,
            "current_year": current_year,
        },
    )


# --- Endpoint POST edycji operatora ---
@router.post("/{operator_id}/edit", name="admin_handle_edit_operator_proxy")
async def handle_edit_operator_proxy_admin(
    request: Request,
    operator_id: int,
    name: str = Form(...),
    contact_person: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
):
    api_data = {
        "name": name,
        "contact_person": contact_person,
        "email": email,
        "phone": phone,
        "address": address,
    }
    # Usuń klucze z None, aby wysłać tylko te pola, które mają być zaktualizowane
    # (jeśli schemat OperatorUpdate ma wszystkie pola opcjonalne)
    api_data_cleaned = {k: v for k, v in api_data.items() if v is not None}

    form_data_for_retry = {
        "id": operator_id,
        **api_data,
    }  # Użyj oryginalnych danych z formularza do ponownego wypełnienia

    async with httpx.AsyncClient() as client:
        try:
            response = await client.put(
                f"{VESSEL_API_BASE_URL}/operators/{operator_id}", json=api_data_cleaned
            )
            response.raise_for_status()
            request.session["flash_success"] = (
                f"Dane operatora (ID: {operator_id}) zostały pomyślnie zaktualizowane."
            )
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json().get("detail", e.response.text)
            except json.JSONDecodeError:
                detail = e.response.text
            if e.response.status_code == 422:
                request.session[f"form_error_operator_edit_{operator_id}"] = (
                    f"Błąd walidacji danych z API: {detail}"
                )
                request.session[f"form_data_operator_edit_{operator_id}"] = (
                    form_data_for_retry
                )
                return RedirectResponse(
                    request.url_for(
                        "admin_serve_edit_operator_form", operator_id=operator_id
                    ),
                    status_code=status.HTTP_303_SEE_OTHER,
                )
            request.session["flash_error"] = (
                f"Błąd API ({e.response.status_code}): {detail}"
            )
        except Exception as e:
            request.session["flash_error"] = f"Nieoczekiwany błąd: {str(e)}"

    return RedirectResponse(
        url=request.url_for("admin_serve_operators_list"),
        status_code=status.HTTP_303_SEE_OTHER,
    )


# --- Endpoint POST usuwania operatora ---
@router.post("/{operator_id}/delete", name="admin_handle_delete_operator_proxy")
async def handle_delete_operator_proxy_admin(request: Request, operator_id: int):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(
                f"{VESSEL_API_BASE_URL}/operators/{operator_id}"
            )
            if response.status_code == status.HTTP_204_NO_CONTENT:
                request.session["flash_success"] = (
                    f"Operator (ID: {operator_id}) został pomyślnie usunięty."
                )
            else:
                response.raise_for_status()
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json().get("detail", e.response.text)
            except json.JSONDecodeError:
                detail = e.response.text
            request.session["flash_error"] = (
                f"Błąd usuwania operatora (status: {e.response.status_code}): {detail}"
            )
        except Exception as e:
            request.session["flash_error"] = (
                f"Nieoczekiwany błąd podczas usuwania operatora: {str(e)}"
            )

    return RedirectResponse(
        url=request.url_for("admin_serve_operators_list"),
        status_code=status.HTTP_303_SEE_OTHER,
    )
