import json
import time
from collections.abc import Callable

from markdownify import markdownify as md

from src.common.log import logger


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


def prepare_doc(doc: dict) -> dict:
    doc = {
        k: str(v) for k, v in doc.items()
        if v is not None and not isinstance(v, (list, dict))
    }
    return doc


def decode_html2text(html_text: str) -> str:
    """
    HTML >> Markdown
    """
    # soup = BeautifulSoup(html_text, "lxml")
    # plain_text = soup.get_text(separator='\n', strip=True)
    result_text = md(html_text)  # HTML to Markdown
    return result_text
