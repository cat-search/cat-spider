import os
from collections import defaultdict

import requests
from sqlalchemy import select, and_

from src.common.db import DbConnManager
from src.common.log import logger
from src.common.mongo import init_mongo
from src.common.settings import settings
from src.common.utils import get_stats
from src.models.vk_filestorage import StorageObject, StorageVersion


def download(stats: dict) -> None:
    """
    ...
    """
    with DbConnManager(settings.vk_db_conn_str_filestorage) as conn:
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
        coll = init_mongo(settings.mongo_collection_file)

        # Create download directory if not exists
        os.mkdir(settings.download_dir) if not os.path.exists(settings.download_dir) else None

        # Iterate over rows and download file one by one
        for i, row in enumerate(conn.execute(query).yield_per(settings.chunk_size)):
            logger.info(f"{i}, {row.id}, {row.name}, {row.link}")
            url: str = f"{settings.filestorage_url}/{row.link}"
            # download file
            with requests.session() as session:
                logger.info(msg := f"Downloading file: {url} ...")
                response = session.get(url, stream=True)
                if response.status_code == 200:
                    filename: str = f"{settings.download_dir}/{row.name}"
                    with open(filename, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    logger.info(f"{msg} done")
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
