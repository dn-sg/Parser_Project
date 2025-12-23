from celery.utils.log import get_task_logger

from src.tasks.celery_app import celery
from src.tasks.db_utils import _log_started, _log_finished
from src.parsers.sources.smartlab import run_smartlab_parser
from src.parsers.sources.rbc import run_rbc_parser
from src.parsers.sources.dohod import run_dohod_parser

logger = get_task_logger(__name__)


@celery.task(bind=True, name="parse_smartlab")
def task_parse_smartlab(self):
    """Task to parse SmartLab stocks"""
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
    """Task to parse RBC news"""
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
    """Task to parse Dohod dividends"""
    log_id = _log_started("Dohod", self.request.id)
    try:
        run_dohod_parser()
        _log_finished(log_id, "SUCCESS")
        return "SUCCESS"
    except Exception as e:
        _log_finished(log_id, "FAIL", str(e))
        raise

