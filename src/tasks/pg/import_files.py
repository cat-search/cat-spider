import subprocess
from collections import defaultdict
from pprint import pformat

from pymongo.errors import DuplicateKeyError
from sqlalchemy import select

from src.common.db import DbConnManager, get_sites
from src.common.log import logger
from src.common.mongo import init_mongo
from src.common.settings import settings
from src.common.utils import get_stats, make_storage_url, prepare_doc
from src.common.vectordb import init_marqo
from src.models.cat_meta import SpiderFile, Status


def parse_doc(file: SpiderFile, stats: dict) -> list[dict] | None:
    """
    Extracts structured text from .doc files with page numbers and paragraphs.
    Returns list of pages with their paragraphs and page numbers.
    """
    file_name: str = file.storage_object_name
    file_path: str = file.target_path
    logger.info(msg := f"Parsing file: {file_path} ...")
    stats[file_name] = defaultdict(int)
    stats = stats[file_name]
    try:
        # Use antiword to extract formatted text with page breaks (^L/form feed character)
        result = subprocess.run(
            ['antiword', '-f', file_path],
            capture_output=True,
            text=True,
            check=True
        )
        full_text = result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(msg := f"Error parsing .doc file: {e}")
        raise AssertionError(msg)
    except FileNotFoundError:
        logger.error(
            msg := (
                "Error: antiword is required but not installed. Install with:\n"
                "sudo apt-get install antiword  # Debian/Ubuntu\n"
                "brew install antiword          # macOS"
            )
        )
        raise AssertionError(msg)

    # Split text into pages using form feed character
    pages = full_text.split('\x0c')
    stats['pages'] = len(pages)

    structured_pages = []
    for page_num, page_content in enumerate(pages, start=1):
        # Clean and split into paragraphs
        paragraphs = [p.strip() for p in page_content.split('\n\n') if p.strip()]

        if paragraphs:  # Skip empty pages
            structured_pages.append({
                'page_number': page_num,
                'paragraphs': paragraphs
            })
            stats[f"page_{page_num}"] = len(paragraphs)

    logger.info(f"{msg} done")
    return structured_pages


def parse(stats: dict) -> None:
    status_id: tuple = (Status.downloaded.value, Status.error.value)

    # Initialize MongoDB client, db, collection
    coll = init_mongo(settings.mongo_collection_page)

    # Initialize VectorDB client
    mq = init_marqo(settings.marqo_index_page)
    idx = mq.index(settings.marqo_index_page)

    with DbConnManager(settings.db_conn_str) as cat_conn:
        sites: dict = {
            str(item.id): item.name for item in get_sites(full=False)
        }

        query = select(
            SpiderFile
        ).where(
            SpiderFile.status_id.in_(status_id),
        ).execution_options(stream_results=True)

        for file_num, file in enumerate(cat_conn.execute(query).yield_per(settings.chunk_size)):
            file = file[0]  # Why is that?
            file_type: str = file.storage_object_name.split('.', maxsplit=1)[-1]
            if file_type == 'doc':
                data = parse_doc(file, stats)
            elif file_type == 'pdf':
                ...
                continue
            elif file_type == 'xlsx':
                ...
                continue
            else:
                raise AssertionError(
                    f"Unknown file type: {file_type}, {file.storage_object_name}"
                )

            for page in data:
                for para_num, paragraph in enumerate(page['paragraphs']):
                    doc = {
                        '_id': f"{file.storage_object_id}-{page}-{paragraph}",
                        'storage_object_id': file.storage_object_id,
                        'name': file.storage_object_name,
                        'site_id': file.storage_object_site_id,
                        'site_name': sites[file.storage_object_site_id],
                        'data': paragraph,
                        'page': page['page_number'],
                        'paragraph': para_num,
                        'link': make_storage_url(file.storage_version_link),
                    }
                    stats['page']['read'] += 1
                    # Insert into VectorDB
                    prepared_doc = prepare_doc(doc)
                    result = idx.add_documents(
                        [prepared_doc],
                        tensor_fields=['name', 'body']
                    )
                    stats['vectordb']['inserted'] += 1
                    logger.info(f"Inserted: {file_num}, {page}, {paragraph}: {result}")

                    try:
                        coll.insert_one(doc)    # Insert document into MongoDB
                        stats['mongo']['inserted'] += 1
                    except DuplicateKeyError:   # Duplicated _id (site_id) in MongoDB
                        stats['mongo']['duplicate_key_error'] += 1

        logger.info(f"index stats:\n{pformat(idx.get_stats())}")


@logger.catch(reraise=True)
def main():
    logger.info("Fetcher started")

    # Statistics
    stats: dict = {
        'page': defaultdict(int),
        'vectordb': defaultdict(int),
        'mongo': defaultdict(int),
    }

    count: int = parse(stats)

    logger.info(get_stats(stats))
    logger.info("Fetcher finished")


if __name__ == '__main__':
    main()
