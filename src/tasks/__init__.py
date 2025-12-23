from src.tasks.celery_app import celery
from src.tasks.parser_tasks import (
    task_parse_smartlab,
    task_parse_rbc,
    task_parse_dohod,
)

__all__ = [
    "celery",
    "task_parse_smartlab",
    "task_parse_rbc",
    "task_parse_dohod",
]
