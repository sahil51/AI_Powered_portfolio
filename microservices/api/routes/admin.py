from fastapi import APIRouter, HTTPException

from monitoring.logger import logger

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/reindex-portfolio")
async def trigger_portfolio_reindex():
    try:
        from application.sync.reindex import reindex_portfolio_data
        from infrastructure.cache.redis_client import get_redis
        from infrastructure.database.session import db

        redis = await get_redis()
        async with db.session_factory() as session:
            result = await reindex_portfolio_data(session, redis)
            await session.commit()

        logger.info(f"Manual reindex triggered: {result}")
        return {"status": "ok", **result}
    except Exception as e:
        logger.error(f"Manual reindex failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
