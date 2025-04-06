import logging
import os
import sys

from loguru import logger

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOGURU_FORMAT = "<level>{level}</level> | " \
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | " \
                "<cyan>{module}</cyan> | " \
                "<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

logger.remove()
error_handler = logger.add(sys.stderr, level=LOG_LEVEL, format=LOGURU_FORMAT)


def log_progress(logger_: logging.Logger, instance: str):
    """
    Log of loading instance to db. Wrapped function have to return counter of inserted rows
    :param logger_: defined logger
    :param instance: db instance loaded to table
    :return:
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger_.info(f'Start loading {instance}')
            counter = func(*args, **kwargs)
            logger_.info(f'{counter} {instance} rows were loaded')
        return wrapper
    return decorator
