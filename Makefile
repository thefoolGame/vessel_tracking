.PHONY: up down build ps logs shell-db shell-alembic db-init migration apply-migration rollback db-schema

# Podstawowe komendy docker-compose
up:
	docker compose up -d

down:
	docker compose down

clean:
	docker compose down -v

build:
	docker compose build

ps:
	docker compose ps

logs:
	docker compose logs -f

# Dostęp do kontenerów
shell-db:
	docker compose exec postgres bash

shell-alembic:
	docker compose exec alembic bash

# Operacje Alembic (SQLAlchemy migracje)
migration:
	@read -p "Migration name: " name; \
	docker compose run --rm alembic revision --autogenerate -m "$$name"

apply-migration:
	docker compose run --rm alembic upgrade head

rollback:
	docker compose run --rm alembic downgrade -1

db-schema:
	docker compose exec postgres pg_dump -U postgres -d vessel_tracking --schema-only > schema.sql
