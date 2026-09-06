.PHONY: create-migration run-migrations seed

create-migration:
	uv run alembic revision --autogenerate -m "description of the change"
run-migrations:
	uv run alembic upgrade head

seed:
	uv run python seed.py
