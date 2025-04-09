from collections import defaultdict

from pymongo.errors import DuplicateKeyError
from sqlalchemy import select, cast, Text

from src.common.db import DbConnManager
from src.common.log import logger
from src.common.mongo import init_mongo
from src.common.settings import settings
from src.common.utils import get_stats, prepare_doc
from src.common.vectordb import init_marqo
from src.models.vk_cms import SiteServiceObject, Page


def import_page(stats: dict) -> None:
    """
    Import pages_page table from DB.
    """
    with DbConnManager(settings.vk_db_conn_str_cms) as conn:
        # Query pages_page + site_service_object
        query = select(
            Page.id.label('page_id'),  # id страницы
            Page.name,
            Page.body,                                    # содержимое страницы
            Page.views_count,                             # Кол-во просмотров
            Page.created_at,
            Page.created_by_id,
            Page.updated_at,
            Page.updated_by_id,
            SiteServiceObject.site_id,
            SiteServiceObject.type                        # page all
            # TODO: We need to add link to the site here
        ).join(
            SiteServiceObject,
            SiteServiceObject.external_id == cast(Page.id, Text),
        ).where(
            SiteServiceObject.site_id.in_(settings.site_ids),  # Our sites
        ).execution_options(stream_results=True)          # Streaming for chunking

        # Initialize MongoDB client, db, collection
        coll = init_mongo(settings.mongo_collection_page)

        # Initialize VectorDB client
        mq = init_marqo(settings.marqo_index_page)
        idx = mq.index(settings.marqo_index_page)

        # Iterate over rows
        for i, row in enumerate(conn.execute(query).yield_per(settings.chunk_size)):
            logger.info(f"{i}, {row.page_id}, {row.name}")
            doc: dict = {
                # _id in MongoDB - unique identifier
                '_id': row.page_id,  # We will use page_id as _id
                'name': row.name,
                'body': row.body,  # содержимое страницы
                'views_count': row.views_count,  # Кол-во просмотров
                'created_at': row.created_at,
                'created_by_id': row.created_by_id,
                'updated_at': row.updated_at,
                'updated_by_id': row.updated_by_id,
                'site_id': row.site_id,
                'type': row.type,  # page all
            }
            try:
                # Insert document into MongoDB
                coll.insert_one(doc)
                stats['site']['inserted'] += 1
                # Duplicated _id (site_id) in MongoDB
            except DuplicateKeyError:
                stats['site']['duplicate_key_error'] += 1

            # TODO: Here we can insert into vector db directly
            # Insert into VectorDB
            idx.add_documents(
                [prepare_doc(doc)],
                tensor_fields=['name', 'body']
            )
            stats['site']['vectordb_inserted'] += 1


@logger.catch(reraise=True)
def main():
    logger.info("Fetcher started")

    # Statistics
    stats: dict = {
        'site': defaultdict(int),
    }

    import_page(stats)

    logger.info(get_stats(stats))
    logger.info("Fetcher finished")


if __name__ == '__main__':
    main()
