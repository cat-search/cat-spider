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
    mq = marqo.Client(
        url=settings.marqo_url,
        main_user=settings.marqo_user,
        main_password=settings.marqo_password,
    )

    if delete_index:  # Housekeeping - Delete the index if it already exists
        try:
            mq.index(index).delete()
        except:
            pass

    # Create an index if it doesn't exist
    if check_index := mq.index(index):
        logger.info(f"Marqo index exists: {index}")
    if create_index and not check_index:
        logger.info(f"Creating marqo index: {index} ...")
        mq.create_index(index, model="hf/e5-base-v2")
    return mq
