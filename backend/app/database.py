from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import Settings, settings


class Base(DeclarativeBase):
    pass


def engine_options(config: Settings) -> dict[str, Any]:
    options: dict[str, Any] = {"pool_pre_ping": True}
    if config.database_url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
        return options
    connect_args: dict[str, str | int] = {"connect_timeout": config.database_connect_timeout}
    if config.database_sslmode and "sslmode=" not in config.database_url:
        connect_args["sslmode"] = config.database_sslmode
    options.update(
        pool_size=config.database_pool_size,
        max_overflow=config.database_max_overflow,
        pool_timeout=config.database_pool_timeout,
        pool_recycle=config.database_pool_recycle,
        connect_args=connect_args,
    )
    return options


engine = create_engine(settings.database_url, **engine_options(settings))
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
