from dataclasses import dataclass, field

from sqlalchemy import text

from infrastructure.database.session import db
from monitoring.logger import logger


@dataclass
class HealthStatus:
    connected: bool = False
    pool_size: int = 0
    pool_checked_in: int = 0
    pool_checked_out: int = 0
    pool_overflow: int = 0
    migration_version: str | None = None
    errors: list[str] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        return self.connected and not self.errors


class DatabaseHealthChecker:
    async def check(self) -> HealthStatus:
        status = HealthStatus()

        try:
            async with db.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                status.connected = True
        except Exception as e:
            status.errors.append(f"Connection failed: {e}")
            logger.error(f"Health check connection failed: {e}")

        try:
            pool_status = db.engine.pool.status()
            status.pool_size = pool_status.get("size", 0)
            status.pool_checked_in = pool_status.get("checked_in", 0)
            status.pool_checked_out = pool_status.get("checked_out", 0)
            status.pool_overflow = pool_status.get("overflow", 0)
        except Exception as e:
            status.errors.append(f"Pool status failed: {e}")

        try:
            async with db.engine.connect() as conn:
                result = await conn.execute(
                    text("SELECT version_num FROM alembic_version")
                )
                row = result.fetchone()
                if row:
                    status.migration_version = str(row[0])
        except Exception:
            status.migration_version = None

        return status

    async def check_connection(self) -> bool:
        try:
            async with db.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    async def get_pool_stats(self) -> dict:
        try:
            pool_status = db.engine.pool.status()
            return {
                "size": pool_status.get("size", 0),
                "checked_in": pool_status.get("checked_in", 0),
                "checked_out": pool_status.get("checked_out", 0),
                "overflow": pool_status.get("overflow", 0),
            }
        except Exception as e:
            return {"error": str(e)}

    async def get_migration_version(self) -> str | None:
        try:
            async with db.engine.connect() as conn:
                result = await conn.execute(
                    text("SELECT version_num FROM alembic_version")
                )
                row = result.fetchone()
                return str(row[0]) if row else None
        except Exception:
            return None


health_checker = DatabaseHealthChecker()
