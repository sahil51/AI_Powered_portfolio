from celery import current_app

from application.sync.checksum import has_portfolio_changed, save_checksum
from application.sync.reindex import reindex_portfolio_data
from infrastructure.cache.redis_client import get_redis
from infrastructure.database.session import db
from tasks.base import AppBaseTask


@current_app.task(
    bind=True,
    base=AppBaseTask,
    queue="maintenance",
    name="portfolio.reindex_if_changed",
    max_retries=3,
    default_retry_delay=60,
)
def reindex_portfolio_if_changed(self) -> dict:
    import asyncio

    async def _run() -> dict:
        await db.initialize()
        redis = await get_redis()

        async with db.session_factory() as session:
            changed, current_checksum = await has_portfolio_changed(session, redis)
            if not changed:
                return {"status": "skipped", "reason": "No changes detected"}

            result = await reindex_portfolio_data(session, redis)
            await session.commit()
            await save_checksum(redis, current_checksum)

        return {"status": "reindexed", **result}

    return asyncio.run(_run())


@current_app.task(
    bind=True,
    base=AppBaseTask,
    queue="maintenance",
    name="portfolio.force_reindex",
)
def force_reindex_portfolio(self) -> dict:
    import asyncio

    async def _run() -> dict:
        await db.initialize()
        redis = await get_redis()

        async with db.session_factory() as session:
            result = await reindex_portfolio_data(session, redis)
            await session.commit()

        return {"status": "reindexed", **result}

    return asyncio.run(_run())
