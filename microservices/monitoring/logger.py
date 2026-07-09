import logging
import sys

from config.settings import settings


class CorrelationIDFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, "correlation_id"):
            record.correlation_id = "-"
        return True


def setup_logging():
    log_format = "%(asctime)s | %(levelname)-8s | %(correlation_id)-36s | %(name)s | %(message)s"
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(log_format))
    handler.addFilter(CorrelationIDFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level)
    root_logger.addHandler(handler)

    return root_logger


logger = logging.getLogger("ai_assistant")
