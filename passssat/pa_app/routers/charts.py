import random

from fastapi import APIRouter, Request

from fastapi.responses import HTMLResponse

from pa_app.utils.utils import templates


router = APIRouter(prefix="", tags=[""])


@router.get("/chart-data", response_class=HTMLResponse, name="sensors_page")
async def get_chart_data(request: Request):
    data = {"labels": ["Jan", "Feb", "Mar", "Apr"], "values": [10, 20, 30, 40]}
    context = {"request": request, "data": data}
    return templates.TemplateResponse("index_chart.html", context)


@router.get("/fetch_battery_data")
def fetch_battery_data():
    data = {
        "labels": [
            "31-03-25 13:00",
            "31-03-25 14:00",
            "31-03-25 15:00",
            "31-03-25 16:00",
        ],
        "values": [
            random.uniform(1.0, 9.0),
            random.uniform(1.0, 9.0),
            random.uniform(1.0, 9.0),
            random.uniform(1.0, 9.0),
        ],
    }
    return data


@router.get("/fetch_battery_data_1")
def fetch_battery_data_1():
    data = {
        "labels": [
            "31-03-25 13:00",
            "31-03-25 14:00",
            "31-03-25 15:00",
            "31-03-25 16:00",
        ],
        "values": [
            random.uniform(1.0, 9.0),
            random.uniform(1.0, 9.0),
            random.uniform(1.0, 9.0),
            random.uniform(1.0, 9.0),
        ],
    }
    return data


@router.get("/fetch_battery_data_2")
def fetch_battery_data_2():
    data = {
        "labels": [
            "31-03-25 13:00",
            "31-03-25 14:00",
            "31-03-25 15:00",
            "31-03-25 16:00",
        ],
        "values": [
            random.uniform(1.0, 9.0),
            random.uniform(1.0, 9.0),
            random.uniform(1.0, 9.0),
            random.uniform(1.0, 9.0),
        ],
    }
    return data


@router.get("/fetch_battery_data_3")
def fetch_battery_data_3():
    data = {
        "labels": [
            "31-03-25 13:00",
            "31-03-25 14:00",
            "31-03-25 15:00",
            "31-03-25 16:00",
        ],
        "values": [
            random.uniform(1.0, 9.0),
            random.uniform(1.0, 9.0),
            random.uniform(1.0, 9.0),
            random.uniform(1.0, 9.0),
        ],
    }
    return data


@router.get("/fetch_battery_data_4")
def fetch_battery_data_4():
    data = {
        "labels": [
            "31-03-25 13:00",
            "31-03-25 14:00",
            "31-03-25 15:00",
            "31-03-25 16:00",
        ],
        "values": [
            random.uniform(1.0, 9.0),
            random.uniform(1.0, 9.0),
            random.uniform(1.0, 9.0),
            random.uniform(1.0, 9.0),
        ],
    }
    return data


@router.get("/fetch_steering_data")
def fetch_steering_data1():
    data = {
        "labels": [
            "31-03-25 13:00",
            "31-03-25 14:00",
            "31-03-25 15:00",
            "31-03-25 16:00",
        ],
        "values": [
            random.choice([0, 1]),
            random.choice([0, 1]),
            random.choice([0, 1]),
            random.choice([0, 1]),
        ],
    }
    return data

