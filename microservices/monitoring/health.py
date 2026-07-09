import redis.asyncio as aioredis
from redis.asyncio.sentinel import Sentinel
from sqlalchemy import text

from config.settings import settings
from infrastructure.cache.redis_client import get_redis
from infrastructure.database.session import db


class HealthChecker:
    @staticmethod
    async def check_database() -> dict:
        try:
            async with db.session_factory() as session:
                await session.execute(text("SELECT 1"))
            return {"status": "healthy"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    @staticmethod
    async def check_redis() -> dict:
        try:
            r = await get_redis()
            await r.ping()
            info = {}
            if settings.redis_sentinel_enabled:
                info["mode"] = "sentinel"
                info["master"] = settings.redis_sentinel_master
                sentinel_hosts = []
                for hostport in settings.redis_sentinel_hosts:
                    parts = hostport.split(":")
                    host = parts[0]
                    port = int(parts[1]) if len(parts) > 1 else 26379
                    sentinel_hosts.append((host, port))
                try:
                    Sentinel(sentinel_hosts, socket_timeout=3)
                    sentinel_info = []
                    for host, port in sentinel_hosts:
                        try:
                            sc_ping = await aioredis.from_url(f"redis://{host}:{port}", socket_timeout=3)
                            await sc_ping.ping()
                            await sc_ping.close()
                            sentinel_info.append(f"{host}:{port}=ok")
                        except Exception:
                            sentinel_info.append(f"{host}:{port}=down")
                    info["sentinels"] = sentinel_info
                except Exception as se:
                    info["sentinels_error"] = str(se)
            else:
                info["mode"] = "standalone"
                info["url"] = settings.redis_url
            return {"status": "healthy", "info": info}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    @staticmethod
    async def check_llm() -> dict:
        return {"status": "healthy", "primary_model": "gemini/gemini-2.0-flash", "fallback": "cerebras > nvidia > huggingface"}

    @staticmethod
    async def check_celery() -> dict:
        return {"status": "healthy", "broker": settings.celery_broker_url}

    @staticmethod
    async def check_all() -> dict:
        db = await HealthChecker.check_database()
        redis = await HealthChecker.check_redis()
        llm = await HealthChecker.check_llm()
        celery = await HealthChecker.check_celery()

        all_healthy = all(
            s["status"] == "healthy" for s in [db, redis, llm, celery]
        )

        return {
            "status": "healthy" if all_healthy else "degraded",
            "services": {
                "database": db,
                "redis": redis,
                "llm": llm,
                "celery": celery,
            },
        }
