from pprint import pformat

import marqo
from src.common.settings import settings
from src.common.log import logger


def init_marqo(
        index: str,
        model: str = settings.marqo_model,
        create_index: bool = True,
        delete_index: bool = False,
) -> marqo.Client:
    # Create a Marqo client
    logger.info(f"Initializing marqo client: {settings.marqo_url} ...")
    mq: marqo.Client = marqo.Client(
        url=settings.marqo_url,
        # main_user=settings.marqo_user,
        api_key=settings.marqo_api_key,
        # main_password=settings.marqo_password,
    )

    if delete_index:  # Housekeeping - Delete the index if it already exists
        try:
            mq.index(index).delete()
        except Exception as e:
            pass

    results = mq.get_indexes().get('results', [])
    logger.info(f"Marqo indexes: {results}")
    indexes = set(
        [item.get('indexName') for item in results]
    )

    # Create an index if it doesn't exist
    if check_index := index in indexes:
        logger.info(f"Marqo index exists: {index}")

    if create_index and not check_index:
        logger.info(msg := f"Creating marqo index: {index} ...")
        index_settings = settings.marqo_index_settings
        index_settings['model'] = settings.marqo_model
        logger.info(f"settings:\n{pformat(settings.marqo_index_settings)}")
        mq.create_index(
            index,
            settings_dict=index_settings,
            wait_for_readiness=False,       # To avoid failure on create_index
        )
        logger.info(f"{msg} done")
    return mq
