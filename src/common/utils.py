import json
import re
import time
from collections.abc import Callable
from hashlib import md5

from langchain.text_splitter import CharacterTextSplitter
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from markdownify import markdownify as md

from src.common.log import logger
from src.common.settings import settings


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


def make_storage_url(file_link: str) -> str:
    return f"{settings.filestorage_url}/{file_link}"


def make_hash(object_id, page, paragraph) -> str:
    return md5(
        f"{str(object_id).replace('-', '')}{page}{paragraph}"
    ).hexdigest()


def write_text_file(file_path: str, data: str, stats: dict) -> str:
    file_name: str = file_path.rsplit('/', maxsplit=1)[-1]
    new_filename: str = f"{file_path}.txt"
    logger.info(f"Writing text to file: {new_filename} ...")

    with open(f"{new_filename}", 'w') as f:
        f.write(data)
        stats['fs']['written'] += 1
    return new_filename


def preprocess_text(text: str) -> str:
    """
    Очистка текста от лишних символов
    """
    # Удаление специальных символов
    text = re.sub(r'[\x00-\x1F\x7F-\x9F]', ' ', text)
    # Замена множественных пробелов и переносов
    text = re.sub(r'\s+', ' ', text)
    # Удаление лишних дефисов в переносах
    text = re.sub(r'(\w)-\s(\w)', r'\1\2', text)
    return text.strip()


def chunkate_text_ts(text: str) -> list[Document]:
    """
    Chunkating with CharacterTextSplitter
    """
    logger.info(msg := f"Chunkating text: {len(text)} chars ...")
    text_splitter = CharacterTextSplitter(
        chunk_size=settings.text_chunk_size,
        chunk_overlap=settings.text_chunk_overlap,
        # separators=settings.text_chunk_separators,
    )
    chunks: list[Document]  = text_splitter.create_documents([text])
    logger.info(f"{msg} done: {len(chunks)} chunks")
    return chunks


def chunkate_text_rcts(text: str) -> list[Document]:
    """
    Chunkating with RecursiveCharacterTextSplitter
    """
    logger.info(msg := f"Chunkating text: {len(text)} chars ...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.text_chunk_size,
        chunk_overlap=settings.text_chunk_overlap,
        separators=settings.text_chunk_separators,
    )
    chunks: list[Document]  = text_splitter.create_documents([text])
    logger.info(f"{msg} done: {len(chunks)} chunks")
    return chunks

