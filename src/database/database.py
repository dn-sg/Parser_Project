"""
Асинхронное подключение к базе данных через SQLAlchemy + asyncpg
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from typing import AsyncGenerator, Optional
import os

from src.database.models import Base

# Инициализация движков
_async_engine: Optional[object] = None
_sync_engine: Optional[object] = None


def _get_config():
    """Ленивый импорт config для избежания циклических зависимостей"""
    from src.core.config import config
    return config


def get_async_engine():
    """Получение асинхронного движка (ленивая инициализация)"""
    global _async_engine
    if _async_engine is None:
        config = _get_config()
        _async_engine = create_async_engine(
            config.ASYNC_DATABASE_URL,
            echo=False,
            future=True,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
    return _async_engine


def get_sync_engine():
    """Получение синхронного движка (ленивая инициализация)"""
    global _sync_engine
    if _sync_engine is None:
        config = _get_config()
        _sync_engine = create_engine(
            config.DATABASE_URL,
            echo=False,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
    return _sync_engine

# Фабрики сессий
_AsyncSessionLocal: Optional[async_sessionmaker] = None
_SessionLocal: Optional[sessionmaker] = None


def get_async_sessionmaker():
    """Получение фабрики асинхронных сессий"""
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        _AsyncSessionLocal = async_sessionmaker(
            get_async_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _AsyncSessionLocal


def get_sessionmaker():
    """Получение фабрики синхронных сессий"""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_sync_engine(),
            autocommit=False,
            autoflush=False,
        )
    return _SessionLocal


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency для FastAPI - получение асинхронной сессии БД
    """
    async_session_maker = get_async_sessionmaker()
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_session():
    """
    Получение синхронной сессии БД для Celery задач
    """
    session_maker = get_sessionmaker()
    return session_maker()


async def init_db():
    """
    Инициализация БД (создание таблиц)
    """
    async_engine = get_async_engine()
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

