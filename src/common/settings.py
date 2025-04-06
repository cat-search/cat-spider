from pydantic import computed_field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Project settings.
    """
    log_level: str                    = 'INFO'
    project_name: str                 = 'cat-spider'

    vk_db_conn_str_cms: str           = 'postgresql://postgres:postgres@localhost:5433/cms'
    vk_db_conn_str_filestorage: str   = 'postgresql://postgres:postgres@localhost:5433/filestorage'
    vk_db_conn_str_lists: str         = 'postgresql://postgres:postgres@localhost:5433/lists'
    # mongo_host: str                 = '127.0.0.1'
    # mongo_port: int                 = 27017
    # mongo_db_name: str              = 'raw'
    # mongo_collection: str           = ''

    chunk_size: int                   = 10    # Chunk size for DB operations


settings = Settings()
