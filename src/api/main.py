import os
from typing import Optional, List, Dict, Any

import pg8000.dbapi
from fastapi import FastAPI, HTTPException
from celery.result import AsyncResult

from src.tasks import celery, task_parse_smartlab, task_parse_rbc, task_parse_dohod

app = FastAPI(title="Parser Project API")


def get_conn():
    return pg8000.dbapi.connect(
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST", "db"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB"),
    )


@app.get("/")
def home():
    return {"message": "API is running", "docs": "/docs"}


@app.post("/api/run/{source}")
def run_parser(source: str):
    source = source.lower().strip()

    if source == "smartlab":
        task = task_parse_smartlab.delay()
    elif source == "rbc":
        task = task_parse_rbc.delay()
    elif source == "dohod":
        task = task_parse_dohod.delay()
    else:
        raise HTTPException(status_code=400, detail="Unknown source. Use: smartlab|rbc|dohod")

    return {"message": "Task started", "task_id": task.id, "source": source}


@app.get("/api/task/{task_id}")
def task_status(task_id: str):
    res = AsyncResult(task_id, app=celery)
    payload = {"task_id": task_id, "state": res.state}
    if res.ready():
        payload["result"] = str(res.result)
    return payload


@app.get("/api/stats")
def stats():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT count(*) FROM smartlab_stocks;")
    smartlab_total = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM rbc_news;")
    rbc_total = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM dohod_divs;")
    dohod_total = cur.fetchone()[0]

    conn.close()
    return {"smartlab_total": smartlab_total, "rbc_total": rbc_total, "dohod_total": dohod_total}


@app.get("/api/data/smartlab")
def smartlab_data(limit: int = 200):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, name, ticker, last_price_rub, price_change_percent, volume_mln_rub, parsed_at
        FROM smartlab_stocks
        ORDER BY parsed_at DESC, id DESC
        LIMIT %s;
        """,
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "name": r[1],
            "ticker": r[2],
            "last_price_rub": float(r[3]) if r[3] is not None else None,
            "price_change_percent": float(r[4]) if r[4] is not None else None,
            "volume_mln_rub": float(r[5]) if r[5] is not None else None,
            "parsed_at": r[6],
        }
        for r in rows
    ]


@app.get("/api/data/rbc")
def rbc_data(limit: int = 50):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, title, url, parsed_at
        FROM rbc_news
        ORDER BY parsed_at DESC, id DESC
        LIMIT %s;
        """,
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()

    return [{"id": r[0], "title": r[1], "url": r[2], "parsed_at": r[3]} for r in rows]


@app.get("/api/data/dohod")
def dohod_data(limit: int = 200):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, ticker, company_name, sector, period, payment_per_share, currency, yield_percent,
               record_date_estimate, capitalization_mln_rub, dsi, parsed_at
        FROM dohod_divs
        ORDER BY parsed_at DESC, id DESC
        LIMIT %s;
        """,
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "ticker": r[1],
            "company_name": r[2],
            "sector": r[3],
            "period": r[4],
            "payment_per_share": float(r[5]) if r[5] is not None else None,
            "currency": r[6],
            "yield_percent": float(r[7]) if r[7] is not None else None,
            "record_date_estimate": r[8],
            "capitalization_mln_rub": float(r[9]) if r[9] is not None else None,
            "dsi": float(r[10]) if r[10] is not None else None,
            "parsed_at": r[11],
        }
        for r in rows
    ]


@app.get("/api/logs")
def api_logs(limit: int = 200):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT l.id, s.name, s.url, l.celery_task_id, l.status,
               l.items_parsed, l.started_at, l.finished_at, l.duration_seconds,
               l.error_code, l.error_message
        FROM logs l
        JOIN source s ON s.id = l.source_id
        ORDER BY l.started_at DESC NULLS LAST, l.id DESC
        LIMIT %s;
        """,
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "source_name": r[1],
            "source_url": r[2],
            "celery_task_id": r[3],
            "status": r[4],
            "items_parsed": r[5],
            "started_at": r[6],
            "finished_at": r[7],
            "duration_seconds": r[8],
            "error_code": r[9],
            "error_message": r[10],
        }
        for r in rows
    ]


@app.get("/api/status")
def api_status():
    """
    Последний статус по каждому source (RBC/SmartLab/Dohod)
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT s.id, s.name, s.url,
               l.status, l.started_at, l.finished_at, l.duration_seconds, l.error_message
        FROM source s
        LEFT JOIN (
            SELECT DISTINCT ON (source_id)
                source_id, status, started_at, finished_at, duration_seconds, error_message
            FROM logs
            ORDER BY source_id, started_at DESC NULLS LAST, id DESC
        ) l ON l.source_id = s.id
        ORDER BY s.id;
        """
    )
    rows = cur.fetchall()
    conn.close()

    return [
        {
            "source_id": r[0],
            "name": r[1],
            "url": r[2],
            "status": r[3] or "NO_RUNS",
            "started_at": r[4],
            "finished_at": r[5],
            "duration_seconds": r[6],
            "error_message": r[7],
        }
        for r in rows
    ]

@app.get("/api/rbc_news/{news_id}")
def rbc_news_one(news_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, title, url, text, parsed_at
        FROM rbc_news
        WHERE id = %s
        """,
        (news_id,),
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="News not found")

    return {
        "id": row[0],
        "title": row[1],
        "url": row[2],
        "text": row[3],
        "parsed_at": row[4],
    }


@app.get("/api/data/smartlab/history")
def smartlab_history(ticker: str, limit: int = 50000):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT parsed_at, last_price_rub
        FROM smartlab_stocks
        WHERE ticker = %s AND last_price_rub IS NOT NULL
        ORDER BY parsed_at ASC, id ASC
        LIMIT %s;
    """, (ticker, limit))
    rows = cur.fetchall()
    conn.close()
    return [{"parsed_at": r[0], "last_price_rub": float(r[1])} for r in rows]
