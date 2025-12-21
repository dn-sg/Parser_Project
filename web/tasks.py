"""
Celery задачи для парсинга
Использует SQLAlchemy вместо RAW SQL
"""
import os
from celery import Celery
from celery.utils.log import get_task_logger
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from infra.database import get_db_session
from models.log import Log
from models.source import Source
from parsers.smartlab import run_smartlab_parser
from parsers.rbc import run_rbc_parser
from parsers.dohod import run_dohod_parser

logger = get_task_logger(__name__)

redis_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
celery = Celery("tasks", broker=redis_url, backend=redis_url)


def _get_source_id(session, source_name: str) -> int:
    """Получение ID источника через SQLAlchemy"""
    source = session.query(Source).filter(Source.name == source_name).first()
    if not source:
        raise RuntimeError(f"Source '{source_name}' not found in table source")
    return source.id


def _log_started(source_name: str, celery_task_id: str) -> int:
    """Логирование начала задачи через SQLAlchemy"""
    with get_db_session() as session:
        source_id = _get_source_id(session, source_name)
        from datetime import datetime
        log = Log(
            source_id=source_id,
            celery_task_id=celery_task_id,
            status="STARTED",
            started_at=datetime.utcnow()
        )
        session.add(log)
        session.commit()
        session.refresh(log)
        return log.id


def _log_finished(log_id: int, status: str, error_message: str | None = None):
    """Логирование завершения задачи через SQLAlchemy"""
    with get_db_session() as session:
        log = session.query(Log).filter(Log.id == log_id).first()
        if not log:
            logger.error(f"Log with id {log_id} not found")
            return
        
        from datetime import datetime
        log.status = status
        log.error_message = error_message
        log.finished_at = datetime.utcnow()
        
        if log.started_at:
            duration = (log.finished_at - log.started_at).total_seconds()
            log.duration_seconds = int(duration)
        
        session.commit()


@celery.task(bind=True, name="parse_smartlab")
def task_parse_smartlab(self):
    log_id = _log_started("SmartLab", self.request.id)
    try:
        run_smartlab_parser()
        _log_finished(log_id, "SUCCESS")
        return "SUCCESS"
    except Exception as e:
        _log_finished(log_id, "FAIL", str(e))
        raise


@celery.task(bind=True, name="parse_rbc")
def task_parse_rbc(self):
    log_id = _log_started("RBC", self.request.id)
    try:
        run_rbc_parser()
        _log_finished(log_id, "SUCCESS")
        return "SUCCESS"
    except Exception as e:
        _log_finished(log_id, "FAIL", str(e))
        raise


@celery.task(bind=True, name="parse_dohod")
def task_parse_dohod(self):
    log_id = _log_started("Dohod", self.request.id)
    try:
        run_dohod_parser()
        _log_finished(log_id, "SUCCESS")
        return "SUCCESS"
    except Exception as e:
        _log_finished(log_id, "FAIL", str(e))
        raise
