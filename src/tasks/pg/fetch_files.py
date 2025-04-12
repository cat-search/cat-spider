import os
from collections import defaultdict

import requests
from sqlalchemy import select, and_

from src.common.db import DbConnManager, file_register, file_set_status
from src.common.log import logger
from src.common.mongo import init_mongo
from src.common.settings import settings
from src.common.utils import get_stats
from src.models.vk_filestorage import StorageObject, StorageVersion
from src.models.cat_meta import Status


def download(stats: dict) -> None:
    """
    ...
    """
    with (
        DbConnManager(settings.vk_db_conn_str_filestorage) as vk_conn,
        DbConnManager(settings.db_conn_str) as cat_conn
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

        # Initialize MongoDB client, db, collection
        # coll = init_mongo(settings.mongo_collection_file)

        # Create download directory if not exists
        os.mkdir(settings.download_dir) if not os.path.exists(settings.download_dir) else None

        # Iterate over rows and download file one by one
        for i, row in enumerate(vk_conn.execute(query).yield_per(settings.chunk_size)):
            logger.info(f"{i}, {row.id}, {row.name}, {row.link}")
            url: str = f"{settings.filestorage_url}/{row.link}"
            filename: str = f"{settings.download_dir}/{row.name}"
            file_register(cat_conn, row, filename, Status.new.value)

            # download file
            with requests.session() as session:
                logger.info(msg := f"Downloading file: {url} ...")
                response = session.get(url, stream=True)
                if response.status_code == 200:
                    with open(filename, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    logger.info(f"{msg} done")
                    file_set_status(cat_conn, row.id, Status.downloaded.value)
                    stats['file']['downloaded'] += 1
                else:
                    raise AssertionError(f"Failed to download file: {url}")


@logger.catch(reraise=True)
def main():
    logger.info("Fetcher started")

    # Statistics
    stats: dict = {
        'file': defaultdict(int),
    }

    download(stats)

    logger.info(get_stats(stats))
    logger.info("Fetcher finished")


if __name__ == '__main__':
    main()
