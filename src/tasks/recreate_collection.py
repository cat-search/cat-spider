from src.common.log import logger
from src.vectordb.weaviate_vdb import init_weaviate, delete_collection, create_collection


@logger.catch(reraise=True)
def main():
    logger.info("Recreate_collection started")

    with init_weaviate() as wc:
        delete_collection(wc)
        create_collection(wc)

    logger.info("Recreate_collection finished")


if __name__ == '__main__':
    main()
