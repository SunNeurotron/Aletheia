import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# Import Base from your application's models module
from Aletheia_v3.infrastructure.models import Base as AletheiaBase # Use an alias if 'Base' is too generic
target_metadata = AletheiaBase.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_url():
    """Return the database URL from an environment variable, falling back to alembic.ini."""
    # This allows overriding the URL from alembic.ini with an environment variable.
    # Useful for different environments (dev, test, prod).
    # The env var name should match what you use in your app (e.g., from docker-compose).
    # For Aletheia_v3, let's assume 'ALETHEIA_V3_DATABASE_URL'.
    db_url_env_var = "ALETHEIA_V3_DATABASE_URL" # Make sure this matches your actual env var name

    # Get URL from alembic.ini as a fallback if env var is not set
    default_url = config.get_main_option("sqlalchemy.url")

    url = os.getenv(db_url_env_var, default_url)

    # Alembic/SQLAlchemy might log the URL including password.
    # Consider logging a masked version if necessary, though typically this script's output is not public.
    # print(f"DEBUG: Database URL for Alembic: {url}") # For debugging only
    return url

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url() # Use the helper to get the URL
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
    # Use a dictionary for configuration suitable for engine_from_config
    cfg = config.get_section(config.config_ini_section)
    cfg["sqlalchemy.url"] = get_url() # Override with URL from env var or ini

    connectable = engine_from_config(
        cfg, # Use the modified configuration dictionary
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
```
