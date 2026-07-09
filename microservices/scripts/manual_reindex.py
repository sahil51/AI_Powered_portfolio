import asyncio

from infrastructure.cache.redis_client import get_redis
from infrastructure.database.session import DatabaseEngine
from monitoring.logger import logger
from application.sync.reindex import reindex_portfolio_data


async def main():
    logger.info("Manual reindex: starting...")

    engine = DatabaseEngine()
    await engine.initialize()
    redis = await get_redis()

    async with engine.session_factory() as session:
        result = await reindex_portfolio_data(session, redis)
        await session.commit()
        logger.info(f"Reindex complete: {result}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
