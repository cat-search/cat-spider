from sqlalchemy import select
import time

from src.common.db import DbConnManager
from src.common.log import logger
from src.common.settings import settings
from src.tasks.fetch_files import main as fetch_files
from src.tasks.import_files import main as import_files
from src.tasks.import_sites import main as import_site
from src.tasks.import_pages import main as import_page
from src.vectordb.weaviate_vdb import init_weaviate


@logger.catch(reraise=True)
def main():
    logger.info("Spider started")

    logger.info(msg_db := f"Check Postgresql DB connection: {settings.db_conn_str} ...")
    logger.info(
        msg_vdb := f"Check Vector DB connection: {settings.weaviate_host}:{settings.weaviate_port} ..."
    )

    db_ready, vdb_ready = False, False
    while True:
        if not db_ready:
            try:
                with DbConnManager(settings.db_conn_str) as conn:
                    res = conn.execute(select(1))
                    if res.rowcount == 1:
                        logger.info(f"{msg_db} OK")
                        db_ready = True
            except Exception as e:
                logger.warning(f"DB isn't ready yet: {e}")
                logger.info("Waiting 10 seconds...")
                time.sleep(settings.db_startup_check_interval)

        if not vdb_ready:
            try:
                wc = init_weaviate()
                if wc.is_ready():
                    logger.info(f"{msg_vdb} OK")
                    vdb_ready = True
            except Exception as e:
                logger.warning(f"VectorDB isn't ready yet: {e}")
                logger.info("Waiting 10 seconds...")
                time.sleep(settings.vdb_startup_check_interval)

        if db_ready and vdb_ready:
            break

    logger.info("Checks passed: OK")


if __name__ == '__main__':
    main()
