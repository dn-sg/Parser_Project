"""
FastAPI application with async database connections using SQLAlchemy
"""
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Depends
from celery.result import AsyncResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct
from sqlalchemy.orm import selectinload

from src.tasks import celery, task_parse_smartlab, task_parse_rbc, task_parse_dohod
from src.database import (
    get_async_session,
    Source,
    Log,
    RBCNews,
    SmartlabStock,
    DohodDiv,
)

app = FastAPI(title="Parser Project API")


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
async def stats(session: AsyncSession = Depends(get_async_session)):
    """Получение статистики по всем источникам"""
    smartlab_count = await session.scalar(select(func.count(SmartlabStock.id)))
    rbc_count = await session.scalar(select(func.count(RBCNews.id)))
    dohod_count = await session.scalar(select(func.count(DohodDiv.id)))
    
    return {
        "smartlab_total": smartlab_count or 0,
        "rbc_total": rbc_count or 0,
        "dohod_total": dohod_count or 0
    }


@app.get("/api/data/smartlab")
async def smartlab_data(
    limit: int = 200,
    session: AsyncSession = Depends(get_async_session)
):
    """Получение данных об акциях SmartLab"""
    stmt = (
        select(SmartlabStock)
        .order_by(SmartlabStock.parsed_at.desc(), SmartlabStock.id.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    stocks = result.scalars().all()
    
    return [
        {
            "id": stock.id,
            "name": stock.name,
            "ticker": stock.ticker,
            "last_price_rub": float(stock.last_price_rub) if stock.last_price_rub is not None else None,
            "price_change_percent": float(stock.price_change_percent) if stock.price_change_percent is not None else None,
            "volume_mln_rub": float(stock.volume_mln_rub) if stock.volume_mln_rub is not None else None,
            "parsed_at": stock.parsed_at,
        }
        for stock in stocks
    ]


@app.get("/api/data/rbc")
async def rbc_data(
    limit: int = 50,
    session: AsyncSession = Depends(get_async_session)
):
    """Получение новостей RBC"""
    stmt = (
        select(RBCNews)
        .order_by(RBCNews.parsed_at.desc(), RBCNews.id.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
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
    session: AsyncSession = Depends(get_async_session)
):
    """Получение данных о дивидендах Dohod"""
    stmt = (
        select(DohodDiv)
        .order_by(DohodDiv.parsed_at.desc(), DohodDiv.id.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    divs = result.scalars().all()
    
    return [
        {
            "id": div.id,
            "ticker": div.ticker,
            "company_name": div.company_name,
            "sector": div.sector,
            "period": div.period,
            "payment_per_share": float(div.payment_per_share) if div.payment_per_share is not None else None,
            "currency": div.currency,
            "yield_percent": float(div.yield_percent) if div.yield_percent is not None else None,
            "record_date_estimate": div.record_date_estimate,
            "capitalization_mln_rub": float(div.capitalization_mln_rub) if div.capitalization_mln_rub is not None else None,
            "dsi": float(div.dsi) if div.dsi is not None else None,
            "parsed_at": div.parsed_at,
        }
        for div in divs
    ]


@app.get("/api/logs")
async def api_logs(
    limit: int = 200,
    session: AsyncSession = Depends(get_async_session)
):
    """Получение логов выполнения парсеров"""
    stmt = (
        select(Log, Source)
        .join(Source, Log.source_id == Source.id)
        .order_by(Log.started_at.desc().nullslast(), Log.id.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
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
async def api_status(session: AsyncSession = Depends(get_async_session)):
    """
    Последний статус по каждому source (RBC/SmartLab/Dohod)
    """
    # Получаем все источники
    sources_stmt = select(Source).order_by(Source.id)
    sources_result = await session.execute(sources_stmt)
    sources = sources_result.scalars().all()
    
    result = []
    for source in sources:
        # Получаем последний лог для каждого источника
        log_stmt = (
            select(Log)
            .where(Log.source_id == source.id)
            .order_by(Log.started_at.desc().nullslast(), Log.id.desc())
            .limit(1)
        )
        log_result = await session.execute(log_stmt)
        log = log_result.scalar_one_or_none()
        
        result.append({
            "source_id": source.id,
            "name": source.name,
            "url": source.url,
            "status": log.status if log else "NO_RUNS",
            "started_at": log.started_at if log else None,
            "finished_at": log.finished_at if log else None,
            "duration_seconds": log.duration_seconds if log else None,
            "error_message": log.error_message if log else None,
        })
    
    return result


@app.get("/api/rbc_news/{news_id}")
async def rbc_news_one(
    news_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Получение одной новости RBC по ID"""
    stmt = select(RBCNews).where(RBCNews.id == news_id)
    result = await session.execute(stmt)
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


@app.get("/api/data/smartlab/history")
async def smartlab_history(
    ticker: str,
    limit: int = 50000,
    session: AsyncSession = Depends(get_async_session)
):
    """Получение истории цен акции по тикеру"""
    stmt = (
        select(SmartlabStock.parsed_at, SmartlabStock.last_price_rub)
        .where(
            SmartlabStock.ticker == ticker,
            SmartlabStock.last_price_rub.isnot(None)
        )
        .order_by(SmartlabStock.parsed_at.asc(), SmartlabStock.id.asc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    rows = result.all()
    
    return [
        {
            "parsed_at": row[0],
            "last_price_rub": float(row[1]) if row[1] is not None else None
        }
        for row in rows
    ]
