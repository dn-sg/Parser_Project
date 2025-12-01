import os
from celery import Celery

redis_url = os.environ.get('REDIS_URL', 'redis://redis:6379/0')

app = Celery('tasks', broker=redis_url, backend=redis_url)

@app.task
def parse_website_task(url):
    return f"parsing {url} (TEST)"
