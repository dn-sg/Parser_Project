"""
Celery tasks
"""
import os
import time

import pg8000.dbapi
from celery import Celery
from celery.utils.log import get_task_logger

from src.parsers.sources.smartlab import run_smartlab_parser
from src.parsers.sources.rbc import run_rbc_parser
from src.parsers.sources.dohod import run_dohod_parser

logger = get_task_logger(__name__)

redis_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
celery = Celery("tasks", broker=redis_url, backend=redis_url)


def _get_conn():
    return pg8000.dbapi.connect(
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST", "db"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB"))


def _get_source_id(cur, source_name: str) -> int:
    cur.execute("SELECT id FROM source WHERE name = %s LIMIT 1;", (source_name,))
    row = cur.fetchone()
    if not row:
        raise RuntimeError(f"Source '{source_name}' not found in table source")
    return row[0]


def _log_started(source_name: str, celery_task_id: str) -> int:
    conn = _get_conn()
    cur = conn.cursor()

    source_id = _get_source_id(cur, source_name)
    cur.execute(
        """
        INSERT INTO logs (source_id, celery_task_id, status, started_at)
        VALUES (%s, %s, %s, NOW())
        RETURNING id;
        """,
        (source_id, celery_task_id, "STARTED"),
    )
    log_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return log_id


def _log_finished(log_id: int, status: str, error_message: str | None = None):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE logs
        SET status = %s,
            error_message = %s,
            finished_at = NOW(),
            duration_seconds = EXTRACT(EPOCH FROM (NOW() - started_at))::int
        WHERE id = %s;
        """,
        (status, error_message, log_id),
    )
    conn.commit()
    conn.close()


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
