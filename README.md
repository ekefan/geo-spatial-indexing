# Geo-spatial indexing

## Database and migrations

Run from the project root:

```bash
uv sync
cp .env.example .env
docker compose up -d postgres
uv run alembic upgrade head
uv run alembic current
uv run alembic check
```

Compose uses PostgreSQL 16 with PostGIS installed. The initial migration enables
`postgis` and `pg_trgm` before creating tables and indexes. The database role
needs permission to create extensions; managed databases may require an admin.
