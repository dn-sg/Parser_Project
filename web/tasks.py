import os
import time
from celery import Celery
from celery.utils.log import get_task_logger

# Импортируем твои функции запуска (обрати внимание на путь)
# Так как в Docker папка parsers смонтирована в /app/parsers, импорт будет работать
from parsers.smartlab import run_smartlab_parser
from parsers.rbc import run_rbc_parser
from parsers.dohod import run_dohod_parser

# Настройка логгера
logger = get_task_logger(__name__)

# Инициализация Celery
# Берем настройки из переменных окружения (они есть в docker-compose)
redis_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
celery = Celery('tasks', broker=redis_url, backend=redis_url)

@celery.task(bind=True, name="parse_smartlab")
def task_parse_smartlab(self):
    """Задача запуска парсера SmartLab"""
    logger.info("Start parsing SmartLab")
    try:
        run_smartlab_parser()
        return "Success"
    except Exception as e:
        logger.error(f"Error parsing SmartLab: {e}")
        # Можно добавить запись ошибки в таблицу logs здесь
        raise self.retry(exc=e, countdown=60, max_retries=3)

@celery.task(bind=True, name="parse_rbc")
def task_parse_rbc(self):
    """Задача запуска парсера RBC"""
    logger.info("Start parsing RBC")
    try:
        run_rbc_parser()
        return "Success"
    except Exception as e:
        logger.error(f"Error parsing RBC: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)

@celery.task(bind=True, name="parse_dohod")
def task_parse_dohod(self):
    """Задача запуска парсера Dohod"""
    logger.info("Start parsing Dohod")
    try:
        run_dohod_parser()
        return "Success"
    except Exception as e:
        logger.error(f"Error parsing Dohod: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)
