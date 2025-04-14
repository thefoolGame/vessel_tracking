# System Monitoringu Floty Łodzi

Repozytorium zawiera model i implementację bazy danych PostgreSQL/PostGIS dla systemu monitoringu floty łodzi w czasie rzeczywistym.

## Spis treści

- [Opis projektu](#opis-projektu)
- [Struktura projektu](#struktura-projektu)
- [Model danych](#model-danych)
- [Technologie](#technologie)
- [Instalacja i uruchomienie](#instalacja-i-uruchomienie)
- [Dostęp do bazy danych](#dostęp-do-bazy-danych)

## Opis projektu

Baza danych zaprojektowana do przechowywania i zarządzania danymi dotyczącymi monitoringu floty łodzi. System obsługuje różne typy łodzi, śledząc ich stan techniczny, lokalizację oraz parametry ruchu. Umożliwia przechowywanie danych z systemów AIS oraz planowanie tras poprzez definiowanie przyszłych punktów nawigacyjnych.

## Struktura projektu

```
vessel_tracking/
├── alembic/                     # Katalog zawierający konfigurację migracji
│   ├── alembic.ini              # Plik konfiguracyjny Alembic
│   ├── Dockerfile               # Definicja obrazu Docker dla Alembic
│   ├── migrations/              # Katalog z migracjami bazy danych
│   │   ├── env.py               # Środowisko wykonawcze migracji
│   │   ├── script.py.mako       # Szablon skryptu migracji
│   │   └── versions/            # Wersje migracji
│   └── models.py                # Modele SQLAlchemy
├── database/                    # Katalog z konfiguracją bazy danych
│   ├── init/                    # Skrypty inicjalizacyjne PostgreSQL
│   └── pgadmin-servers.json     # Konfiguracja serwerów PgAdmin
├── docker-compose.yaml          # Konfiguracja usług Docker
└── Makefile                     # Skrypty pomocnicze
```

## Model danych

Obecnie zaimplementowane encje:

### Producent (Manufacturer)

- Przechowuje informacje o producentach łodzi i czujników
- Atrybuty: nazwa, kraj, dane kontaktowe, strona internetowa

### Operator

- Podmioty zarządzające flotami łodzi
- Atrybuty: nazwa, osoba kontaktowa, email, telefon, adres

### Flota (Fleet)

- Zdefiniowane grupy łodzi pod wspólnym zarządem
- Relacja: należy do jednego operatora

### Typ łodzi (VesselType)

- Kategorie łodzi określające ich charakterystykę i parametry techniczne
- Atrybuty: nazwa, opis, producent, wymiary (długość, szerokość, zanurzenie), maksymalna prędkość

### Łódź (Vessel)

- Główne jednostki floty
- Atrybuty: nazwa, typ łodzi, flota, operator, rok produkcji, numery identyfikacyjne (rejestracyjny, IMO, MMSI), sygnał wywoławczy, status
- Walidacje: zapewnienie spójności relacji łódź-flota-operator

### Planowane implementacje

Model danych będzie rozszerzony o następujące encje:

- Czujniki i Typy Czujników
- Odczyty Czujników
- Dane AIS
- Lokalizacje
- Planowane Punkty Trasy
- Dane Pogodowe
- Parametry Łodzi
- Konserwacje
- Alerty
- Konfiguracje Czujników

## Technologie

- **PostgreSQL 17** z rozszerzeniem **PostGIS 3.4** - do obsługi danych przestrzennych
- **SQLAlchemy** - ORM do interakcji z bazą danych
- **Alembic** - narzędzie do migracji bazy danych
- **Docker** i **Docker Compose** - konteneryzacja środowiska
- **PgAdmin 4** - narzędzie administracyjne dla PostgreSQL

## Instalacja i uruchomienie

Projekt korzysta z Makefile'a, który zawiera szereg pomocniczych komend ułatwiających pracę z projektem:

```bash
# Klonowanie repozytorium
git clone https://github.com/thefoolGame/vessel_tracking.git
cd vessel-tracking

# Uruchomienie z Docker Compose
make up

# Sprawdzenie stanu kontenerów
make ps

# Wykonanie migracji Alembic
make apply-migration
```

## Dostęp do bazy danych

### PostgreSQL

- **Host**: localhost
- **Port**: 5432
- **Baza danych**: vessel_tracking
- **Użytkownik**: postgres
- **Hasło**: postgres_password

### PgAdmin 4

- **URL**: <http://localhost:5050>
- **Email**: <admin@vessel-tracking.com>
- **Hasło**: pgadmin_password

Po zalogowaniu masz dostęp do serwera "Vessel Tracking Database" skonfigurowanego automatycznie.

## Backend
- **Port** 8000
- **Docs** localhost:8000/docs
- Testowanie Api na docsach lub Postman