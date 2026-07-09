import asyncio
from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from infrastructure.database.config import DatabaseConfig, db_config
from infrastructure.database.exceptions import ConnectionError
from monitoring.logger import logger


class Base(DeclarativeBase):
    pass


class DatabaseEngine:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self._config = config or db_config
        self._engine = None
        self._session_factory = None
        self._connected = False

    async def initialize(self) -> None:
        if self._engine is not None:
            return

        connect_args: dict = {
            "timeout": self._config.pool_timeout,
            **self._config.ssl_args,
        }

        self._engine = create_async_engine(  # type: ignore[assignment]
            self._config.url,
            echo=self._config.echo,
            pool_size=self._config.pool_size,
            max_overflow=self._config.max_overflow,
            pool_timeout=self._config.pool_timeout,
            pool_recycle=self._config.pool_recycle,
            pool_pre_ping=self._config.pool_pre_ping,
            connect_args=connect_args,
        )

        self._session_factory = async_sessionmaker(  # type: ignore[assignment]
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        await self._validate_connection()
        self._connected = True
        logger.info("Database engine initialized and connected")

    async def _validate_connection(self) -> None:
        last_exception: Exception | None = None
        for attempt in range(1, self._config.max_retries + 1):
            try:
                async with self.engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))
                return
            except Exception as e:
                last_exception = e
                logger.warning(f"Connection attempt {attempt}/{self._config.max_retries} failed: {e}")
                if attempt < self._config.max_retries:
                    await asyncio.sleep(self._config.retry_delay)

        raise ConnectionError(
            message=f"Failed to connect to database after {self._config.max_retries} attempts",
            detail=str(last_exception),
        )

    async def dispose(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            self._connected = False
            logger.info("Database engine disposed")

    @property
    def engine(self):
        if self._engine is None:
            raise ConnectionError(message="Database engine not initialized. Call initialize() first.")
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        if self._session_factory is None:
            raise ConnectionError(message="Session factory not initialized. Call initialize() first.")
        return self._session_factory

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def config(self) -> DatabaseConfig:
        return self._config


db: DatabaseEngine = DatabaseEngine()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with db.session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_transaction_session() -> AsyncIterator[AsyncSession]:
    async with db.session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    await db.initialize()
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def get_async_session() -> async_sessionmaker[AsyncSession]:
    return db.session_factory
