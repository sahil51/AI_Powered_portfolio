from abc import ABC, abstractmethod
from typing import Any

from monitoring.logger import logger


class BaseTool(ABC):
    name: str = ""
    description: str = ""

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        pass

    async def run(self, **kwargs) -> Any:
        logger.info(f"Tool '{self.name}' executing", extra={"kwargs": kwargs})
        try:
            result = await self.execute(**kwargs)
            logger.info(f"Tool '{self.name}' succeeded", extra={"result": result})
            return result
        except Exception as e:
            logger.error(f"Tool '{self.name}' failed: {e}", exc_info=True)
            raise
