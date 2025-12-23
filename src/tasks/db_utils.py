"""
Database utilities for Celery tasks
"""
import os
import pg8000.dbapi


def _get_conn():
    """Get database connection"""
    return pg8000.dbapi.connect(
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST", "db"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB"))


def _get_source_id(cur, source_name: str) -> int:
    """Get source ID by name"""
    cur.execute("SELECT id FROM source WHERE name = %s LIMIT 1;", (source_name,))
    row = cur.fetchone()
    if not row:
        raise RuntimeError(f"Source '{source_name}' not found in table source")
    return row[0]


def _log_started(source_name: str, celery_task_id: str) -> int:
    """Log task start"""
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
    """Log task finish"""
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

