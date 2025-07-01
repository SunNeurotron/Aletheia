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

# Add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
# target_metadata = None

# For autogenerate support, import your Base and your models so that
# Alembic knows about them.
# Adjust the import path to where your Base and models are defined.
# This should point to the Base object from your infrastructure.sqlalchemy_repository
import sys
# Construct the path to the 'aletheia_stats' module root from 'alembic' directory
# alembic_stats/alembic/env.py -> ../.. -> aletheia_stats_module_root
module_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if module_root not in sys.path:
    sys.path.insert(0, module_root)

# Now, import Base from your application structure
# This assumes 'aletheia_stats_module_root' is the parent of 'aletheia_stats' package.
# If aletheia_stats_module_root is 'SunNeurotron/Aletheia/aletheia_stats', then
# the package is 'aletheia_stats.aletheia_stats.infrastructure.sqlalchemy_repository'
# However, if the script_location for alembic is 'alembic' inside 'aletheia_stats' directory,
# and 'aletheia_stats' is in PYTHONPATH, then we can import more directly.

# Assuming the 'aletheia_stats' directory (which contains alembic.ini and this alembic dir)
# is the root for the 'aletheia_stats' package context.
from aletheia_stats.aletheia_stats.infrastructure.sqlalchemy_repository import Base as StatsBase # Renamed to avoid conflict
target_metadata = StatsBase.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def get_database_url():
    return os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))

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
        configuration = {} # Ensure configuration is a dictionary
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = engine_from_config(
        configuration, # Use the modified configuration
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
