# Alembic env.py para [Module Name]
# (Copia y adapta el alembic/env.py de aletheia_stats/alembic/env.py)
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Ajustar el path para importar Base desde la ubicación correcta de los modelos del módulo
# Ejemplo: from ..module_name.infrastructure.sqlalchemy_models import Base
# target_metadata = Base.metadata
target_metadata = None  # Placeholder - El usuario debe configurar esto


def get_module_database_url():
    # Priorizar MODULE_DATABASE_URL, luego DATABASE_URL (si es compartido), luego config
    return os.getenv(
        "MODULE_DATABASE_URL",
        os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url")),
    )


def run_migrations_offline() -> None:
    url = get_module_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    if configuration is None:
        configuration = {}
    configuration["sqlalchemy.url"] = get_module_database_url()

    connectable = engine_from_config(
        configuration,
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
