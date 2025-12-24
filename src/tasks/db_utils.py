from datetime import datetime
from src import get_sync_session, Source, Log



def _get_source_by_name(session, source_name: str) -> Source:
    """Get source by name"""
    source = session.query(Source).filter(Source.name == source_name).first()
    if not source:
        raise RuntimeError(f"Source '{source_name}' not found in table source")
    return source


def _log_started(source_name: str, celery_task_id: str) -> int:
    """Log task"""
    session = get_sync_session()
    try:
        source = _get_source_by_name(session, source_name)
        
        log = Log(
            source_id=source.id,
            celery_task_id=celery_task_id,
            status="STARTED",
            started_at=datetime.utcnow(),
        )
        session.add(log)
        session.commit()
        session.refresh(log)
        return log.id
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _log_finished(log_id: int, status: str, error_message: str | None = None, items_parsed: int = 0):
    """Log task finish"""
    session = get_sync_session()
    try:
        log = session.query(Log).filter(Log.id == log_id).first()
        if not log:
            raise RuntimeError(f"Log with id {log_id} not found")
        
        log.status = status
        log.error_message = error_message
        log.finished_at = datetime.utcnow()
        log.items_parsed = items_parsed
        
        # Вычисляю длительность в секундах
        if log.started_at and log.finished_at:
            duration = (log.finished_at - log.started_at).total_seconds()
            log.duration_seconds = int(duration)
        
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
