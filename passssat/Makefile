PROFILE ?= local

COMMON_COMPOSE_FILE := docker-compose.common.yml
BASE_COMPOSE_FILE := docker-compose.base.yml
SERVER_COMPOSE_FILE := docker-compose.server.yml

ifeq ($(PROFILE), server)
	COMPOSE_FILES := -f $(COMMON_COMPOSE_FILE) -f $(SERVER_COMPOSE_FILE)
	COMPOSE_PROFILE_FLAG := 
	TARGET_SERVICES := passat_app_server 
else ifeq ($(PROFILE), local)
	COMPOSE_FILES := -f $(COMMON_COMPOSE_FILE) -f $(BASE_COMPOSE_FILE)
	COMPOSE_PROFILE_FLAG := --profile local
	TARGET_SERVICES := passat_app_local 
else
    $(error "Nieznany profil: $(PROFILE). Dostępne: server, local")
endif

DOCKER_COMPOSE_CMD = docker compose $(COMPOSE_FILES) $(COMPOSE_PROFILE_FLAG)
.PHONY: help up down clean build ps logs shell

help:
	@echo "Dostępne komendy:"
	@echo "  make up PROFILE=[server|local]     - Uruchamia kontenery (domyślnie server)"
	@echo "  make down PROFILE=[server|local]   - Zatrzymuje i usuwa kontenery (domyślnie server)"
	@echo "  make clean PROFILE=[server|local]  - Zatrzymuje i usuwa kontenery wraz z wolumenami (domyślnie server)"
	@echo "  make build PROFILE=[server|local]  - Buduje obrazy (domyślnie server)"
	@echo "  make ps PROFILE=[server|local]     - Wyświetla status kontenerów (domyślnie server)"
	@echo "  make logs PROFILE=[server|local]   - Wyświetla logi kontenerów (domyślnie server)"
	@echo "  make shell PROFILE=[server|local] SERVICE=[nazwa_serwisu] - Otwiera shell w kontenerze (domyślnie server)"
	@echo ""
	@echo "Przykład użycia dla profilu lokalnego:"
	@echo "  make up PROFILE=local"
	@echo "  make logs PROFILE=local"

up:
	@echo "Uruchamianie kontenerów dla profilu: $(PROFILE)..."
	$(DOCKER_COMPOSE_CMD) up -d $(TARGET_SERVICES)

down:
	@echo "Zatrzymywanie kontenerów dla profilu: $(PROFILE)..."
	$(DOCKER_COMPOSE_CMD) down $(TARGET_SERVICES)

clean:
	@echo "Zatrzymywanie kontenerów i usuwanie wolumenów dla profilu: $(PROFILE)..."
	$(DOCKER_COMPOSE_CMD) down -v $(TARGET_SERVICES)

build:
	@echo "Budowanie obrazów dla profilu: $(PROFILE)..."
	$(DOCKER_COMPOSE_CMD) build $(TARGET_SERVICES)

ps:
	@echo "Status kontenerów dla profilu: $(PROFILE)..."
	$(DOCKER_COMPOSE_CMD) ps $(TARGET_SERVICES)

logs:
	@echo "Logi kontenerów dla profilu: $(PROFILE)..."
	$(DOCKER_COMPOSE_CMD) logs -f $(TARGET_SERVICES)

SERVICE ?= $(TARGET_SERVICES)
shell:
	@echo "Otwieranie shella w serwisie $(SERVICE) dla profilu: $(PROFILE)..."
	$(DOCKER_COMPOSE_CMD) exec $(SERVICE) /bin/bash

DEFAULT_GOAL := help
