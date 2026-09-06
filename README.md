# Geo-spatial property indexing and Retrieval

This task is focused on designing and implementing a geo-bucket based location normalization system for property search.
Read [DESIGN.md](DESIGN.md) for architecture, bucketing strategy, database schema, location matching logic and operation flow of the system.

## Setup

Requires Python 3.14, uv, and Docker Compose.
```bash
# install uv and make if necessary
bash install-tools.sh
```
 Run from the project root:
```bash
uv sync
cp .env.example .env
docker compose up -d --wait postgres
uv run alembic upgrade head
make seed
uv run uvicorn main:app --app-dir src --reload
```
This sets the project and runs the fastapi http server.
Docker compose sets up postgres with postGIS installed using the postGIS image.

Open [http://localhost:8000/docs](http://localhost:8000/docs) for interactive API documentation.

Cool!! Project Setup is complete.

## Run Tests?

```bash
uv run pytest tests/unit -q
uv run pytest -m integration -q
uv run pytest -m live -v
uv run pytest -q
```

Unit tests mock database dependencies and run without Docker or a configured
database. Integration tests use `Testcontainers` to start a disposable PostGIS
container, apply Alembic migrations, and check the schema before testing real
queries. Docker must be available; Testcontainers pulls images if necessary and
removes its containers afterward. No local database or Compose service is needed.
The test suite ignores your application `DATABASE_DSN` and never uses its rows.