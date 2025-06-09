FROM ubuntu:22.04
SHELL ["/bin/bash", "-c", "-o", "pipefail"]

ENV LANG C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_ROOT_USER_ACTION=ignore \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_HOME='/opt/poetry' \
    TZ="Europe/Warsaw"


RUN apt-get update && \
    apt-get install -y --no-install-recommends python3.10 python3.10-venv curl && \
    rm -rf /var/lib/apt/lists/*

RUN python3 -m venv "$POETRY_HOME"
RUN "$POETRY_HOME/bin/pip" install "poetry==1.8.3"
RUN ln -s "$POETRY_HOME/bin/poetry" /usr/local/bin/poetry

RUN mkdir /app
WORKDIR /app

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-interaction --no-ansi

ENTRYPOINT poetry run uvicorn --host 0.0.0.0 --port 8000 --reload pa_app.main:app
