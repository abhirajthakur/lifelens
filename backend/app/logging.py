import logging
import os
from enum import StrEnum

LOG_FORMAT_DEBUG = "%(levelname)s:  %(message)s: %(pathname)s: %(funcName)s: %(lineno)d"


class LogLevels(StrEnum):
    info = "INFO"
    warn = "WARN"
    error = "ERROR"
    debug = "DEBUG"


def configure_logging(log_level: str = None):
    # Get log level from environment variable or use provided default
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", LogLevels.info)
    log_level = str(log_level).upper()
    log_levels = [level.value for level in LogLevels]

    if log_level not in log_levels:
        logging.basicConfig(level=LogLevels.error)
        return

    if log_level == LogLevels.debug:
        logging.basicConfig(level=log_level, format=LOG_FORMAT_DEBUG)
        return

    logging.basicConfig(level=log_level)
