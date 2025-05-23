from collections import defaultdict

from sqlalchemy import select, cast, Text

from src.common.db import DbConnManager
from src.common.db import compile_sql  # noqa: F401
from src.common.log import logger
from src.common.settings import settings
from src.common.utils import get_stats, decode_html2text, chunkate_text_rcts_plain
from src.models.vk_cms import SiteServiceObject, Page, Site
from src.vectordb.weaviate_vdb import check_collection_readiness, init_weaviate, weaviate_insert_plain


def import_page(stats: dict) -> None:
    """
    Import pages_page table from DB.
    """
    with (
        DbConnManager(settings.vk_db_conn_str_cms) as conn,
        init_weaviate() as wc,
    ):
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
            Site.name.label('site_name'),                 # site name
            SiteServiceObject.type                        # page all
            # TODO: We need to add link to the site here
        ).join(
            SiteServiceObject,
            SiteServiceObject.external_id == cast(Page.id, Text),
        ).join(
            Site,
            Site.id == SiteServiceObject.site_id,
        ).where(
            SiteServiceObject.site_id.in_(settings.site_ids),  # Our sites
        ).execution_options(stream_results=True)          # Streaming for chunking

        # Check if we are able to insert into vdb
        check_collection_readiness(wc)

        # Iterate over each page
        for i, row in enumerate(conn.execute(query).yield_per(settings.chunk_size)):
            # 1. Get object name
            logger.info(f"{i}, {row.page_id}, {row.name}")
            object_name: str = row.name
            stats['source_object'][object_name] = defaultdict(int)

            # 2. Read pages content
            raw_data: str = row.body['data']
            content: str = decode_html2text(raw_data)

            # 4. Chunkate
            text_chunks: list[str] = chunkate_text_rcts_plain(content, stats['vectordb']['chunk'])
            doc_attrs: dict = {
                'object_id': row.page_id,               # page_id as object_id
                'type': 'page',
                'name': row.name,
                'site_id': row.site_id,
                'site_name': row.site_name,             # site name
                'size': len(content),
                'created_at': row.created_at,
                'created_by_id': row.created_by_id,
                'updated_at': row.updated_at,
                'updated_by_id': row.updated_by_id,
                # 'link': None,                         # No links found
                # 'views_count': row.views_count,       # Кол-во просмотров
            }

            # 5. Insert into vector DB
            count: int = weaviate_insert_plain(
                wc, text_chunks, doc_attrs, stats, object_name=object_name,
            )
            stats['source_object'][object_name]['vectordb_inserted'] += count
            stats['source_object'][object_name]['site_name'] = row.site_name


@logger.catch(reraise=True)
def main():
    logger.info("Fetcher started")

    # Statistics
    stats: dict = {
        'vectordb': defaultdict(int),
        'source_object': defaultdict(int),
    }
    stats['vectordb']['chunk'] = defaultdict(int)

    import_page(stats)

    logger.info(get_stats(stats))
    logger.info("Fetcher finished")


if __name__ == '__main__':
    main()
