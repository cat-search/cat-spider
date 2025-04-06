from collections import defaultdict

from sqlalchemy.orm import sessionmaker, Session

from src.common.log import logger
from sqlalchemy import create_engine, MetaData, Table, select, func
from src.models.vk_public import Site
from src.common.settings import settings


def get_sites_site(stats: dict) -> None:
    """
    Gets sites_site table from DB.
    """

    # Create engine and metadata
    engine = create_engine(settings.vk_db_conn_str_cms)
    session_factory = sessionmaker(bind=engine)
    session: Session = session_factory()
    # metadata = MetaData()

    query = select(
        func.count()
    ).select_from(Site).where(
        Site.id.isnot(None),
    )
    count = session.execute(query).scalar()
    logger.info(f"Count of rows in {Site.t_name}: {count}")

    query = select(Site).where(
        Site.id.isnot(None),
    ).execution_options(stream_results=True)    # Streaming for chunking

    for i, row in enumerate(session.execute(query).yield_per(settings.chunk_size)):
        row_data = row[0]
        logger.info(f"{i}, {row_data.id}")
    # Execute the query
    # with engine.connect() as conn:
    #     result = conn.execute(query)
    #     for row in result:
    #         logger.info(row)  # Output: ('joe', 100)


@logger.catch(reraise=True)
def main():
    logger.info("Fetcher started")

    # Statistics
    stats: dict = {
        'deleted': defaultdict(int),
        'inserted': defaultdict(int),
    }

    get_sites_site(stats)

    logger.info("Fetcher finished")


if __name__ == '__main__':
    main()
