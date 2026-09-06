create-migration:
	uv run alembic revision --autogenerate -m "description of the change"
run-migrations:
	uv run alembic upgrade head