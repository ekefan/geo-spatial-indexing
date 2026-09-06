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

If the old `postgres:16` service is running, `docker compose up -d postgres`
recreates it with the new image and retains the named volume. Back up valuable
data before changing images. Do not use `docker compose down -v`: it deletes data.

Alembic reads `DATABASE_DSN` from the environment or the project-root `.env`.
Environment variables take precedence. Both `postgresql://` and
`postgresql+psycopg://` use Psycopg 3. Do not commit `.env`. Inside Compose, use
`postgres:5432` instead of `localhost:5456`.

After changing models:

```bash
uv run alembic revision --autogenerate -m "describe the schema change"
uv run alembic upgrade head
uv run alembic check
```

Review generated migrations before applying them. GeoAlchemy2 hooks render
spatial types and exclude PostGIS extension tables. Direct SQL updates must set
`updated_at` explicitly; the model's `onupdate` applies to SQLAlchemy updates.

To inspect migration SQL without a database connection:

```bash
uv run alembic upgrade head --sql
```

Run offline migration regression checks with `uv run python -m unittest discover
-s tests -v`. These check SQL generation and configuration; `alembic check`
against a running migrated database verifies model/schema agreement.
