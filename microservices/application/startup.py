from application.bootstrap import bootstrap_manager
from application.exceptions import BootstrapError
from monitoring.logger import logger


async def startup() -> None:
    try:
        await bootstrap_manager.bootstrap()
    except BootstrapError:
        logger.error("Application bootstrap failed")
        raise


async def shutdown() -> None:
    await bootstrap_manager.shutdown()
