import os
from collections import defaultdict

from sqlalchemy import select, and_
from weaviate.client import WeaviateClient

from src.common.db import DbConnManager, get_sites
from src.common.log import logger
from src.common.settings import settings
from src.common.utils import (
    get_stats,
    make_storage_url,
    chunkate_text_rcts_plain,
)
from src.models.vk_filestorage import StorageObject, StorageVersion
from src.vectordb.weaviate_vdb import init_weaviate, check_collection_readiness, weaviate_insert_plain


def read_text_file(file_path: str, stats: dict) -> str:
    # Check if file exists on file system
    if not os.path.exists(file_path):
        logger.warning(f"File not found: {file_path}")
        return ''

    logger.info(msg := f"Reading file: {file_path} ...")
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    stats['text_len'] = len(text)
    logger.info(f"{msg} done")
    return text


def load_text_files(stats: dict) -> int:
    wc: WeaviateClient

    with (
        DbConnManager(settings.vk_db_conn_str_filestorage) as vk_conn,
        DbConnManager(settings.db_conn_str) as cat_conn,
        init_weaviate() as wc,
    ):
        query = select(
            StorageObject.id,
            StorageObject.name,                # filename
            StorageObject.context_folder_id,   # папка, определяющая контекст (например, Blog_{id}).
            StorageObject.created_at,
            StorageObject.created_by_id,
            StorageObject.updated_at,
            StorageObject.updated_by_id,
            StorageObject.site_id,
            StorageVersion.size,                # file size
            StorageVersion.link,                # download link
        ).join(
            StorageVersion,
            StorageVersion.id == StorageObject.version_id,
        ).where(
            and_(
                StorageObject.type == 1,                        # Type file
                StorageObject.site_id.in_(settings.site_ids),   # Our sites
            )
        ).execution_options(stream_results=True)  # Streaming for chunking

        sites: dict = {
            str(item.id): item.name for item in get_sites(full=False)
        }

        # Check if we are able to insert into vdb
        check_collection_readiness(wc)

        # Iterate over each file
        file: StorageObject | StorageVersion
        for file_num, file in enumerate(
                vk_conn.execute(query).yield_per(settings.chunk_size)
        ):
            # 1. Get filename
            file_name: str = file.name + '.txt'
            file_path: str = f"{settings.download_dir}/{file_name}"
            stats['file'][file_name] = defaultdict(int)

            # 2. Read file .txt
            content = read_text_file(file_path, stats['file'][file_name])
            if not content:
                continue

            # 4. Chunkate
            text_chunks: list[str] = chunkate_text_rcts_plain(content)
            doc_attrs = {
                'object_id': file.id,
                'type': 'file',
                'name': file.name,
                'site_id': file.site_id,
                'site_name': sites[str(file.site_id)],
                'size': file.size,
                'created_at': file.created_at,
                'created_by_id': str(file.created_by_id),
                'updated_at': file.updated_at,
                'updated_by_id': str(file.updated_by_id),
                'link': make_storage_url(file.link),
            }

            # 5. Insert into vector DB
            count: int = weaviate_insert_plain(
                wc, text_chunks, doc_attrs, stats, file_name=file_name
            )
            stats['file'][file_name]['vectordb_inserted'] += count

            # 6. Insert doc into MongoDB
            # mongo_insert(coll, text_chunks, stats)


@logger.catch(reraise=True)
def main():
    logger.info("Fetcher started")

    # Statistics
    stats: dict = {
        'vectordb': defaultdict(int),  # Inserts into vector db
        'file': defaultdict(int),  # Individual file statistics
    }
    stats['vectordb']['chunk'] = defaultdict(int)

    load_text_files(stats)

    logger.info(get_stats(stats))
    logger.info("Fetcher finished")


if __name__ == '__main__':
    main()
