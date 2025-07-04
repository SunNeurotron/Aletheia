import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
# target_metadata = None

# For autogenerate support, import your Base and your models so that
# Alembic knows about them.
# Adjust the import path to where your Base and models are defined.
# This should point to the Base object from your infrastructure.database
# and ensure models in infrastructure.models are imported so Base.metadata is populated.
import sys

module_root_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
if module_root_path not in sys.path:
    sys.path.insert(0, module_root_path)

from aletheia_stats.aletheia_stats.infrastructure import (  # Ensures models are registered with StatsAppBase.metadata
    models,
)

# Import Base from aletheia_stats.infrastructure.database
# and also import the models from aletheia_stats.infrastructure.models to ensure they are registered
from aletheia_stats.aletheia_stats.infrastructure.database import Base as StatsAppBase

target_metadata = StatsAppBase.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_database_url():
    # Use the same environment variable as the application for consistency
    from aletheia_stats.aletheia_stats.infrastructure.database import (
        SQLALCHEMY_DATABASE_URL as STATS_APP_DB_URL,
    )

    # Alembic's config.get_main_option("sqlalchemy.url") can serve as a fallback if needed,
    # but direct use of the app's configured URL (from env var) is preferred.
    # For simplicity, directly use what the app uses.
    # If STATS_APP_DB_URL is already derived from an env var (like STATS_DATABASE_URL), this is fine.
    # The infrastructure/database.py uses:
    # SQLALCHEMY_DATABASE_URL = os.getenv("STATS_DATABASE_URL", "postgresql://user:pass@localhost:5433/aletheia_stats_db_main_py")
    # So we can reference that environment variable name directly here too.
    return os.getenv(
        "STATS_DATABASE_URL", config.get_main_option("sqlalchemy.url")
    )


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    configuration = config.get_section(config.config_ini_section)
    if configuration is None:
        configuration = {}  # Ensure configuration is a dictionary
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = engine_from_config(
        configuration,  # Use the modified configuration
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
