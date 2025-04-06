import csv
import json
import time
from src.common.log import logger
from collections.abc import Callable


def get_stats(
        stats: dict,
        indent: int = 2,
        sort_keys: bool = True,
        ensure_ascii: bool = False,
) -> str:
    """
    Returns prettified sorted json-like stats converted to str.

    Args:
        stats:  A dictionary with statistics.
        indent: Indentation level for JSON formatting. Default is 2.
        sort_keys: Sort the keys in the JSON output. Default is True.
        ensure_ascii: Escape non-ASCII characters in the JSON output. Default is False.

    Returns: A string in JSON format.
    """
    stats_json = json.dumps(
        stats, indent=indent, sort_keys=sort_keys, ensure_ascii=ensure_ascii
    )
    return f"Statistics:\n{stats_json}"


def timeit(func) -> Callable:

    def wrapped(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logger.info("{}() executed in {:f} s", func.__name__, end - start)
        return result, end - start

    return wrapped
