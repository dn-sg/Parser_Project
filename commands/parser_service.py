"""
Сервис для запуска парсеров с сохранением в БД
Объединяет команды (парсинг) и адаптеры (сохранение)
"""
import logging
from typing import List, Dict
from sqlalchemy.orm import Session
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from infra.database import get_db_session
from adapters.repository import RBCNewsRepository, SmartlabStockRepository, DohodDividendRepository

logger = logging.getLogger(__name__)


class ParserService:
    """Сервис для выполнения парсинга и сохранения данных"""
    
    @staticmethod
    def run_rbc_parser(parser) -> None:
        """Запуск парсера RBC и сохранение данных"""
        try:
            logger.info("Начинаем парсинг RBC...")
            news_list = parser.parse()
            
            if news_list:
                logger.info(f"Спарсено {len(news_list)} новостей.")
                with get_db_session() as session:
                    repository = RBCNewsRepository(session, "RBC")
                    repository.save(news_list)
                    logger.info("Данные сохранены в БД.")
            else:
                logger.warning("Список новостей пуст.")
        except Exception as e:
            logger.error(f"Ошибка запуска RBC: {e}", exc_info=True)
            raise
    
    @staticmethod
    def run_smartlab_parser(parser) -> None:
        """Запуск парсера SmartLab и сохранение данных"""
        try:
            logger.info("Начинаем парсинг SmartLab...")
            data_list = parser.parse()
            
            if data_list:
                logger.info(f"Спарсено {len(data_list)} записей.")
                with get_db_session() as session:
                    repository = SmartlabStockRepository(session, "SmartLab")
                    repository.save(data_list)
                    logger.info("Данные сохранены в БД.")
            else:
                logger.warning("Нет данных для сохранения.")
        except Exception as e:
            logger.error(f"Ошибка запуска SmartLab: {e}", exc_info=True)
            raise
    
    @staticmethod
    def run_dohod_parser(parser) -> None:
        """Запуск парсера Dohod и сохранение данных"""
        try:
            logger.info("Начинаем парсинг Dohod.ru...")
            data = parser.parse()
            
            if data:
                logger.info(f"Спарсено {len(data)} записей.")
                with get_db_session() as session:
                    repository = DohodDividendRepository(session, "Dohod")
                    repository.save(data)
                    logger.info("Данные сохранены в БД.")
            else:
                logger.warning("Пустой результат парсинга.")
        except Exception as e:
            logger.error(f"Ошибка запуска Dohod: {e}", exc_info=True)
            raise

