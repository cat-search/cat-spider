import subprocess
from collections import defaultdict

import PyPDF2
import pandas as pd
from langchain_core.documents import Document
from sqlalchemy import select
from weaviate.client import WeaviateClient

from src.common.db import DbConnManager, get_sites, get_storage_object
from src.common.log import logger
from src.common.settings import settings
from src.common.utils import (
    get_stats,
    make_storage_url,
    write_text_file,
    chunkate_text_rcts,
)
from src.models.cat_meta import SpiderFile, Status
from src.models.vk_filestorage import StorageObject
from src.vectordb.weaviate_vdb import init_weaviate, weaviate_insert, check_collection_readiness


def parse_doc(file: SpiderFile, stats: dict) -> str:
    """
    Extracts structured text from .doc files with page numbers and paragraphs.
    It uses antiword - CLI tool.

    Returns list of pages with their paragraphs and page numbers.
    """
    file_name: str = file.storage_object_name
    file_path: str = file.target_path
    logger.info(msg := f"Parsing file: {file_path} ...")
    if file_name not in stats:
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
                "sudo apt-get install antiword"
            )
        )
        raise AssertionError(msg)

    text_len = len(full_text)
    stats['text_len'] = text_len
    if text_len > 0:
        stats['parsed'] = 1
    logger.info(f"{msg} done")
    return full_text
    # Split text into pages using form feed character
    # pages = full_text.split('\x0c')     # It's not working!!!
    # stats['pages'] = len(pages)
    #
    # structured_pages = []
    # for page_num, page_content in enumerate(pages, start=1):
    #     # Clean and split into paragraphs
    #     paragraphs = [p.strip() for p in page_content.split('\n\n') if p.strip()]
    #
    #     if paragraphs:  # Skip empty pages
    #         structured_pages.append({
    #             'page_number': page_num,
    #             'paragraphs': paragraphs
    #         })
    #         stats[f"page_{page_num}"] = len(paragraphs)


def parse_pdf(file: SpiderFile, stats: dict) -> str:
    """
    Extracts structured text from .pdf files with page numbers and paragraphs.
    Uses PyPDF2 to extract text from PDF files.
    """
    file_name: str = file.storage_object_name
    file_path: str = file.target_path
    logger.info(msg := f"Parsing PDF file: {file_path} ...")
    if file_name not in stats:
        stats[file_name] = defaultdict(int)
    stats = stats[file_name]
    
    try:
        # Open PDF file and read it using PyPDF2
        with open(file_path, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            full_text = ""
            for page_num, page in enumerate(reader.pages):
                # Extract text from each page
                text = page.extract_text()
                if text:
                    full_text += f"Page {page_num + 1}:\n{text}\n\n"
            if not full_text:
                # raise AssertionError("No text extracted from PDF.")
                logger.info(f"Text length: {len(full_text)}")
    except Exception as e:
        logger.error(msg := f"Error parsing PDF file: {e}")
        raise AssertionError(msg)

    text_len = len(full_text)
    stats['text_len'] = text_len
    if text_len > 0:
        stats['parsed'] = 1
    logger.info(f"{msg} done")
    return full_text


def parse_excel(file: SpiderFile, stats: dict) -> str:
    """
    Extracts structured text from .xlsx (Excel) files with sheet names and data.
    Uses pandas to read Excel sheets and convert them into string format.
    """
    file_name: str = file.storage_object_name
    file_path: str = file.target_path
    logger.info(msg := f"Parsing Excel file: {file_path} ...")
    if file_name not in stats:
        stats[file_name] = defaultdict(int)
    stats = stats[file_name]
    
    try:
        # Use pandas to read the Excel file
        df = pd.read_excel(file_path, sheet_name=None)  # Read all sheets into a dictionary
        full_text = ""
        for sheet_name, sheet_data in df.items():
            full_text += f"Sheet: {sheet_name}\n"
            full_text += sheet_data.to_string(index=False) + "\n\n"
        if not full_text:
            raise AssertionError("No text extracted from Excel.")
    except Exception as e:
        logger.error(msg := f"Error parsing Excel file: {e}")
        raise AssertionError(msg)

    text_len = len(full_text)
    stats['text_len'] = text_len
    if text_len > 0:
        stats['parsed'] = 1
    logger.info(f"{msg} done")
    return full_text


def parse(stats: dict) -> int:
    status_id: tuple = (Status.downloaded.value, Status.error.value)

    # Initialize MongoDB client, db, collection
    # coll = init_mongo(settings.mongo_collection_file)

    # Initialize VectorDB client
    # wc: WeaviateClient = init_weaviate()
    # check_collection_readiness(wc)

    wc: WeaviateClient
    with (
        DbConnManager(settings.db_conn_str) as cat_conn,
        init_weaviate() as wc
    ):
        check_collection_readiness(wc)

        sites: dict = {
            str(item.id): item.name for item in get_sites(full=False)
        }

        query = select(
            SpiderFile
        ).where(
            SpiderFile.status_id.in_(status_id),
        ).execution_options(stream_results=True)

        # Iterate over each file
        for file_num, file in enumerate(
                cat_conn.execute(query).yield_per(settings.chunk_size)
        ):
            # 1. Get filename
            file = file[0]          # Get object from Row result
            file_type: str = file.storage_object_name.split('.', maxsplit=1)[-1]
            file_name: str = file.storage_object_name
            stats['file'][file_name] = defaultdict(int)

            # Get StorageObject attributes from filestorage.storage_storageobject table
            so_id: str = file.storage_object_id
            so_attrs: StorageObject = get_storage_object(so_id)

            # 2. Parse file
            if file_type == 'doc':
                # continue
                content = parse_doc(file, stats['file'])   # Parse .doc file
            elif file_type == 'pdf':
                # continue
                content = parse_pdf(file, stats['file'])  # Parse PDF file
            elif file_type == 'xlsx':
                # continue
                content = parse_excel(file, stats['file'])  # Parse Excel file
            else:
                raise AssertionError(
                    f"Unknown file type: {file_type}, {file.storage_object_name}"
                )

            # 3. Let's write whole text to file
            file_path: str = file.target_path
            write_text_file(file_path, content, stats)

            # 4. Chunkate
            text_chunks: list[Document] = chunkate_text_rcts(content)
            doc_attrs = {
                # '_id'               : f"{file.storage_object_id}",
                'object_id'         : file.storage_object_id,
                'type'              : 'file',
                'name'              : file.storage_object_name,
                'site_id'           : file.storage_object_site_id,
                'site_name'         : sites[file.storage_object_site_id],
                'size'              : str(so_attrs.size),
                'created_at'        : so_attrs.created_at,
                'created_by_id'     : str(so_attrs.created_by_id),
                'updated_at'        : so_attrs.updated_at,
                'updated_by_id'     : str(so_attrs.updated_by_id),
                'link'              : make_storage_url(file.storage_version_link),
            }

            # 5. Insert into vector DB
            count: int = weaviate_insert(wc, text_chunks, doc_attrs, stats)
            stats['file'][file_name]['vectordb_inserted'] += count

            # 6. Insert doc into MongoDB
            # mongo_insert(coll, text_chunks, stats)


@logger.catch(reraise=True)
def main():
    logger.info("Fetcher started")

    # Statistics
    stats: dict = {
        'vectordb': defaultdict(int),   # Inserts into vector db
        'mongo': defaultdict(int),      # Inserts into mongodb
        'fs': defaultdict(int),         # File system. If .txt file written
        'file': defaultdict(int),       # Individual file statistics
    }

    parse(stats)

    logger.info(get_stats(stats))
    logger.info("Fetcher finished")


if __name__ == '__main__':
    main()
