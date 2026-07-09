import time

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import Pool

from monitoring.logger import logger


@event.listens_for(Engine, "before_execute")
def _before_execute(conn, clauseelement, multiparams, params):
    conn.info.setdefault("query_start_time", time.time())


@event.listens_for(Engine, "after_execute")
def _after_execute(conn, clauseelement, multiparams, params, result):
    start = conn.info.pop("query_start_time", None)
    if start is not None:
        elapsed = time.time() - start
        if elapsed > 1.0:
            logger.warning(f"Slow query ({elapsed:.2f}s): {clauseelement}")


@event.listens_for(Pool, "checkout")
def _on_checkout(dbapi_conn, conn_record, conn_proxy):
    logger.debug("Database connection checked out from pool")


@event.listens_for(Pool, "checkin")
def _on_checkin(dbapi_conn, conn_record):
    logger.debug("Database connection returned to pool")


@event.listens_for(Pool, "connect")
def _on_connect(dbapi_conn, conn_record):
    logger.debug("New database connection established")
