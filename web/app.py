"""
FastAPI приложение с асинхронной БД
Использует async SQLAlchemy для неблокирующих запросов
"""
import os
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Depends
from celery.result import AsyncResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from infra.database import get_async_db_session
from models.source import Source
from models.log import Log
from models.smartlab_stock import SmartlabStock
from models.rbc_news import RBCNews
from models.dohod_dividend import DohodDividend
from tasks import celery, task_parse_smartlab, task_parse_rbc, task_parse_dohod

app = FastAPI(title="Parser Project API")


@app.get("/")
async def home():
    return {"message": "API is running", "docs": "/docs"}


@app.post("/api/run/{source}")
async def run_parser(source: str):
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
async def task_status(task_id: str):
    res = AsyncResult(task_id, app=celery)
    payload = {"task_id": task_id, "state": res.state}
    if res.ready():
        payload["result"] = str(res.result)
    return payload


@app.get("/api/stats")
async def stats(session: AsyncSession = Depends(get_async_db_session)):
    """Статистика через асинхронный SQLAlchemy"""
    smartlab_total = await session.scalar(select(func.count(SmartlabStock.id)))
    rbc_total = await session.scalar(select(func.count(RBCNews.id)))
    dohod_total = await session.scalar(select(func.count(DohodDividend.id)))
    
    return {
        "smartlab_total": smartlab_total or 0,
        "rbc_total": rbc_total or 0,
        "dohod_total": dohod_total or 0
    }


@app.get("/api/data/smartlab")
async def smartlab_data(
    limit: int = 200,
    session: AsyncSession = Depends(get_async_db_session)
):
    """Данные SmartLab через асинхронный SQLAlchemy"""
    result = await session.execute(
        select(SmartlabStock)
        .order_by(SmartlabStock.parsed_at.desc(), SmartlabStock.id.desc())
        .limit(limit)
    )
    stocks = result.scalars().all()
    
    return [
        {
            "id": stock.id,
            "name": stock.name,
            "ticker": stock.ticker,
            "last_price_rub": float(stock.last_price_rub) if stock.last_price_rub else None,
            "price_change_percent": float(stock.price_change_percent) if stock.price_change_percent else None,
            "volume_mln_rub": float(stock.volume_mln_rub) if stock.volume_mln_rub else None,
            "parsed_at": stock.parsed_at,
        }
        for stock in stocks
    ]


@app.get("/api/data/rbc")
async def rbc_data(
    limit: int = 50,
    session: AsyncSession = Depends(get_async_db_session)
):
    """Данные RBC через асинхронный SQLAlchemy"""
    result = await session.execute(
        select(RBCNews)
        .order_by(RBCNews.parsed_at.desc(), RBCNews.id.desc())
        .limit(limit)
    )
    news = result.scalars().all()
    
    return [
        {
            "id": item.id,
            "title": item.title,
            "url": item.url,
            "parsed_at": item.parsed_at
        }
        for item in news
    ]


@app.get("/api/data/dohod")
async def dohod_data(
    limit: int = 200,
    session: AsyncSession = Depends(get_async_db_session)
):
    """Данные Dohod через асинхронный SQLAlchemy"""
    result = await session.execute(
        select(DohodDividend)
        .order_by(DohodDividend.parsed_at.desc(), DohodDividend.id.desc())
        .limit(limit)
    )
    dividends = result.scalars().all()
    
    return [
        {
            "id": div.id,
            "ticker": div.ticker,
            "company_name": div.company_name,
            "sector": div.sector,
            "period": div.period,
            "payment_per_share": float(div.payment_per_share) if div.payment_per_share else None,
            "currency": div.currency,
            "yield_percent": float(div.yield_percent) if div.yield_percent else None,
            "record_date_estimate": div.record_date_estimate,
            "capitalization_mln_rub": float(div.capitalization_mln_rub) if div.capitalization_mln_rub else None,
            "dsi": float(div.dsi) if div.dsi else None,
            "parsed_at": div.parsed_at,
        }
        for div in dividends
    ]


@app.get("/api/logs")
async def api_logs(
    limit: int = 200,
    session: AsyncSession = Depends(get_async_db_session)
):
    """Логи через асинхронный SQLAlchemy"""
    result = await session.execute(
        select(Log, Source)
        .join(Source, Log.source_id == Source.id)
        .order_by(Log.started_at.desc().nullslast(), Log.id.desc())
        .limit(limit)
    )
    rows = result.all()
    
    return [
        {
            "id": log.id,
            "source_name": source.name,
            "source_url": source.url,
            "celery_task_id": log.celery_task_id,
            "status": log.status,
            "items_parsed": log.items_parsed,
            "started_at": log.started_at,
            "finished_at": log.finished_at,
            "duration_seconds": log.duration_seconds,
            "error_code": log.error_code,
            "error_message": log.error_message,
        }
        for log, source in rows
    ]


@app.get("/api/status")
async def api_status(session: AsyncSession = Depends(get_async_db_session)):
    """Последний статус по каждому source через асинхронный SQLAlchemy"""
    sources_result = await session.execute(select(Source))
    sources = sources_result.scalars().all()
    
    result = []
    for source in sources:
        # Получаем последний лог для источника
        log_result = await session.execute(
            select(Log)
            .filter(Log.source_id == source.id)
            .order_by(Log.started_at.desc().nullslast(), Log.id.desc())
            .limit(1)
        )
        last_log = log_result.scalar_one_or_none()
        
        result.append({
            "source_id": source.id,
            "name": source.name,
            "url": source.url,
            "status": last_log.status if last_log else "NO_RUNS",
            "started_at": last_log.started_at if last_log else None,
            "finished_at": last_log.finished_at if last_log else None,
            "duration_seconds": last_log.duration_seconds if last_log else None,
            "error_message": last_log.error_message if last_log else None,
        })
    
    return result


@app.get("/api/rbc_news/{news_id}")
async def rbc_news_one(
    news_id: int,
    session: AsyncSession = Depends(get_async_db_session)
):
    """Одна новость RBC через асинхронный SQLAlchemy"""
    result = await session.execute(
        select(RBCNews).filter(RBCNews.id == news_id)
    )
    news = result.scalar_one_or_none()
    
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    
    return {
        "id": news.id,
        "title": news.title,
        "url": news.url,
        "text": news.text,
        "parsed_at": news.parsed_at,
    }
