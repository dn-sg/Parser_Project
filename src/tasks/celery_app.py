import os
from celery import Celery

redis_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
celery = Celery("tasks", broker=redis_url, backend=redis_url)

from src.tasks import parser_tasks
