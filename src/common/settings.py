from pydantic import computed_field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Project settings.
    """
    log_level: str                    = 'INFO'
    project_name: str                 = 'cat-spider'

    vk_db_conn_str_cms: str           = 'postgresql://postgres:Oue$8AriEOdN@pg:5432/cms'
    vk_db_conn_str_filestorage: str   = 'postgresql://postgres:Oue$8AriEOdN@pg:5432/filestorage'
    vk_db_conn_str_lists: str         = 'postgresql://postgres:Oue$8AriEOdN@pg:5432/lists'
    db_conn_str: str                  = 'postgresql://postgres:Oue$8AriEOdN@pg:5432/catsearch'
    alembic_db_name: str              = 'catspider'

    mongo_host: str                   = '127.0.0.1'
    mongo_port: int                   = 27017
    mongo_db_name: str                = 'cat'
    mongo_collection_site: str        = 'site'
    mongo_collection_page: str        = 'page'
    mongo_collection_list: str        = 'list'
    mongo_collection_file: str        = 'file'

    chunk_size: int                   = 10    # Chunk size for DB operations

    # ID сайтов, указанных в ТЗ
    site_ids: tuple                   = (
        '83f29091-def2-42a4-82c4-453103d8a457',
        '3d2d628c-0b80-470d-a9fc-f19b353971b7',
        'b7a8428a-9f61-46ff-9fcf-f835a577e1e3',
        '023540f1-15d1-411d-b2c5-3d596089654b',
        '0f11f06b-1c6c-41a8-b30b-1061ce626391',
        '6d111c1d-5d0f-406c-a1e1-74fb2a8acc1d',
        '3b508b32-4c04-4a22-bc4f-94e4bd9f0bdb'
    )

    filestorage_url: str                = 'https://hackaton.hb.ru-msk.vkcloud-storage.ru/media'
    download_dir: str                   = '/opt/catsearch/download'

    # Vector DB. Marqo
    # marqo_url: str                      = "http://cat-vm2.v6.rocks:8081"
    # marqo_user: str                     = "admin"
    # marqo_api_key: str                  = "Hack_the_VK"
    # marqo_model: str                    = "hf/e5-base-v2"
    # # marqo_model: str                    = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    # marqo_index_page: str               = "page_20250409_valer"
    # marqo_index_settings: dict          = {
    #     "textPreprocessing": {
    #         "splitLength": 2,
    #         "splitOverlap": 0,
    #         "splitMethod": "sentence",
    #     },
    # }

    # Vector DB. weaviate
    weaviate_host: str                  = "weaviate"
    # weaviate_host: str                  = "localhost"
    weaviate_port: int                  = 8080
    weaviate_api_key: str               = "Search_the_VK"
    weaviate_collection: str            = "catsearch"
    weaviate_api_endpoint: str          = "http://ollama:11434"
    # Model name. If it's `None`, uses the server-defined default
    # weaviate_model: str                 = None
    weaviate_model: str                 = "nomic-embed-text"

    text_chunk_size: int                = 500
    text_chunk_overlap: int             = 100
    # text_chunk_separators: tuple        = ("\n\n", "\n", r"(?<=\. )", " ", "")
    text_chunk_separators: tuple        = ("\n\n", )

    db_startup_check_interval: int      = 10
    vdb_startup_check_interval: int     = 10


settings = Settings()
