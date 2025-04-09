from collections import defaultdict

from bson.binary import UuidRepresentation
from bson.codec_options import CodecOptions
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from sqlalchemy import select, func

from src.common.db import DbConnManager
from src.common.log import logger
from src.common.settings import settings
from src.common.utils import get_stats
from src.models.vk_cms import Site


def import_site(stats: dict) -> None:
    """
    Import sites_site table from DB.
    """
    with DbConnManager(settings.vk_db_conn_str_cms) as conn:
        # Count rows
        query = select(
            func.count()
        ).select_from(Site).where(
            Site.id.in_(settings.site_ids),
        )
        count = conn.execute(query).scalar()
        stats['site']['total'] = count
        logger.info(f"Count of rows in {Site.t_name}: {count}")

        # Query site_sites
        query = select(
            Site.id,
            Site.name,
            Site.created_by_id,
            Site.created_at,
            Site.updated_by_id,
            Site.updated_at,
        ).where(
            Site.id.in_(settings.site_ids),
        ).execution_options(stream_results=True)    # Streaming for chunking

        # Initialize MongoDB client, db, collection
        client = MongoClient(
            host=settings.mongo_host,
            port=settings.mongo_port,
        )
        db = client.get_database(settings.mongo_db_name)
        python_opts = CodecOptions(uuid_representation=UuidRepresentation.PYTHON_LEGACY)
        coll = db.get_collection(
            settings.mongo_collection_site,
            codec_options=python_opts,
        )
        # Iterate over rows
        for i, row in enumerate(conn.execute(query).yield_per(settings.chunk_size)):
            # row_data = row[0]
            logger.info(f"{i}, {row.id}, {row.name}")
            try:
                doc = {
                    # _id in MongoDB - unique identifier
                    # We will use site_id as _id
                    '_id': row.id,
                    'name': row.name,
                    'created_by_id': row.created_by_id,
                    'created_at': row.created_at,
                    'updated_by_id': row.updated_by_id,
                    'updated_at': row.updated_at,
                }
                coll.insert_one(doc)    # Insert document into MongoDB
                stats['site']['inserted'] += 1
            # Duplicated _id (site_id) in MongoDB
            except DuplicateKeyError:
                stats['site']['duplicate_key_error'] += 1


@logger.catch(reraise=True)
def main():
    logger.info("Fetcher started")

    # Statistics
    stats: dict = {
        'site': defaultdict(int),
    }

    import_site(stats)

    logger.info(get_stats(stats))
    logger.info("Fetcher finished")


if __name__ == '__main__':
    main()
