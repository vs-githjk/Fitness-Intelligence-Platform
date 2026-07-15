from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app import models  # noqa: F401
from app.config import settings
from app.database import Base

config = context.config
migration_url = settings.effective_migration_database_url
# ConfigParser treats percent signs in encoded credentials as interpolation.
config.set_main_option("sqlalchemy.url", migration_url.replace("%", "%%"))
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=migration_url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connect_args: dict[str, str | int] = {}
    if not migration_url.startswith("sqlite"):
        connect_args["connect_timeout"] = settings.database_connect_timeout
        if settings.database_sslmode and "sslmode=" not in migration_url:
            connect_args["sslmode"] = settings.database_sslmode
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_offline() if context.is_offline_mode() else run_migrations_online()
