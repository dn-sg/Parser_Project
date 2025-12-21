"""
Подключение к базе данных через SQLAlchemy
Поддерживает синхронные и асинхронные подключения
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from contextlib import asynccontextmanager, contextmanager
from typing import Generator, AsyncGenerator
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from .config import config
from models.base import Base

# Синхронное подключение (для Celery и legacy кода)
sync_engine = create_engine(config.database_url, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# Асинхронное подключение (для FastAPI)
async_engine = create_async_engine(config.async_database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Database:
    """Класс для работы с базой данных"""
    
    def __init__(self):
        self.engine = sync_engine
        self.async_engine = async_engine
        self.SessionLocal = SessionLocal
        self.AsyncSessionLocal = AsyncSessionLocal
    
    def create_tables(self):
        """Создание всех таблиц (синхронно)"""
        Base.metadata.create_all(bind=self.engine)
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Контекстный менеджер для получения синхронной сессии БД"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Асинхронный контекстный менеджер для получения сессии БД"""
        async with self.AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    def get_source_id(self, session: Session, source_name: str) -> int:
        """Получение ID источника по имени (синхронно)"""
        from models.source import Source
        
        source = session.query(Source).filter(Source.name == source_name).first()
        if not source:
            raise ValueError(f"Источник '{source_name}' не найден в таблице source")
        return source.id


# Глобальный экземпляр для удобства
db = Database()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Функция-хелпер для получения синхронной сессии БД"""
    session = db.SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Асинхронная функция-хелпер для получения сессии БД"""
    async with db.get_async_session() as session:
        yield session
