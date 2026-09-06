import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
from database.models import Base
from dotenv import load_dotenv
from alembic.util import CommandError
from copy import copy
from geoalchemy2 import Geography, Geometry, alembic_helpers

load_dotenv()
# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

database_dsn = os.environ.get("DATABASE_DSN")
if not database_dsn:
    raise CommandError("Set DATABASE_DSN in your environment or .env file")
config.set_main_option("sqlalchemy.url", database_dsn.replace("%", "%%"))
# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

# Tables owned by the postgis/postgis_tiger_geocoder extensions.
# These are created by CREATE EXTENSION, not by our models, so
# autogenerate must never propose dropping or altering them.
TIGER_TABLES = {
    "faces", "county", "county_lookup", "state", "state_lookup", "place",
    "place_lookup", "edges", "addr", "addrfeat", "zip_lookup", "zip_lookup_all",
    "zip_lookup_base", "zip_state", "zip_state_loc", "zcta5", "cousub",
    "countysub_lookup", "tabblock", "tabblock20", "tract", "bg", "topology",
    "layer", "pagc_gaz", "pagc_lex", "pagc_rules", "featnames", "direction_lookup",
    "secondary_unit_lookup", "street_type_lookup", "loader_lookuptables",
    "loader_platform", "loader_variables", "geocode_settings",
    "geocode_settings_default", "spatial_ref_sys",
}


def include_object(object, name, type_, reflected, compare_to):
    """Exclude PostGIS/TIGER-owned tables from autogenerate comparisons."""
    if type_ == "table" and name in TIGER_TABLES:
        return False
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        render_item=render_item,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            render_item=render_item,
        )

        with context.begin_transaction():
            context.run_migrations()


def render_item(type_, obj, autogen_context):
    if type_ == "type" and isinstance(obj, (Geography, Geometry)):
        obj = copy(obj)
        obj.spatial_index = False
    return alembic_helpers.render_item(type_, obj, autogen_context)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
