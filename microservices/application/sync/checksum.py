import hashlib

from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

PORTFOLIO_TABLES = [
    "portfolio_heroinfo",
    "portfolio_project",
    "portfolio_experience",
    "portfolio_skill",
    "portfolio_skillcategory",
    "portfolio_education",
    "portfolio_blogpost",
    "portfolio_contactmethod",
]

CHECKSUM_REDIS_KEY = "portfolio:checksum"


async def get_portfolio_checksum(session: AsyncSession) -> str:
    hasher = hashlib.sha256()
    for table in PORTFOLIO_TABLES:
        rows = await session.execute(sa_text(f"SELECT * FROM {table} ORDER BY id"))
        for row in rows:
            hasher.update(str(dict(row._mapping)).encode())
    return hasher.hexdigest()


async def has_portfolio_changed(session: AsyncSession, redis_client) -> tuple[bool, str]:
    from monitoring.logger import logger

    current = await get_portfolio_checksum(session)
    try:
        stored = redis_client.get(CHECKSUM_REDIS_KEY)
        if stored and stored.decode() == current:
            return False, current
    except Exception as e:
        logger.warning(f"Failed to read portfolio checksum from Redis: {e}")

    return True, current


async def save_checksum(redis_client, checksum: str) -> None:
    redis_client.set(CHECKSUM_REDIS_KEY, checksum)
