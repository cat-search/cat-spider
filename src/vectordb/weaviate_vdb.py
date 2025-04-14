import uuid

from langchain_core.documents import Document
from weaviate import WeaviateClient
from weaviate import connect_to_local as weaviate_connect_to_local
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.init import Auth
from weaviate.collections import Collection

from src.common.log import logger
from src.common.settings import settings


def init_weaviate() -> WeaviateClient:
    """ Инициализация подключения """
    client: WeaviateClient = weaviate_connect_to_local(
        host=settings.weaviate_host,  # Use a string to specify the host
        port=settings.weaviate_port,
        auth_credentials=Auth.api_key(settings.weaviate_api_key),
        # additional_headers={"X-Ollama-Api-Key": "ollama"}
        skip_init_checks=True,
    )
    if not client.is_ready():
        logger.error(msg := f"Weaviate client initialization failed")
        raise AssertionError(msg)

    create_collection(client, settings.weaviate_collection)
    return client


def create_collection(
        client: WeaviateClient, name: str = settings.weaviate_collection,
) -> None:
    """
    Create a collection in weaviate if it doesn't exist

    We use native create() because we use multiple vector fields.
    """
    logger.info(msg := f"Creating weaviate collection: {name} ...")

    # Check if collection exists in weaviate
    if client.collections.exists(name):
        logger.info(f"Collection {name} already exists: OK")
        return

    try:
        collection: Collection = client.collections.create(
            name,
            properties=[
                # ID - It seems that it's an internal document identifier
                # TODO: Do we need to make a hash(object_id + chunk)???
                #   How to avoid duplicates?????????
                Property(name="uuid", data_type=DataType.UUID),
                # content: chunk of text
                Property(name="content", data_type=DataType.TEXT),
                # Name, title
                Property(name="name", data_type=DataType.TEXT),
                # Type: site, page, file, list
                Property(name="type", data_type=DataType.TEXT),
                # Metadata fields
                Property(
                    name="metadata", data_type=DataType.OBJECT,
                    nested_properties=[
                        # Object id (site id, page id, file id, list id)
                        Property(name="object_id", data_type=DataType.UUID),
                        # Page number
                        Property(name="page", data_type=DataType.INT),
                        # Chunk number
                        Property(name="chunk_id", data_type=DataType.INT),
                        # 'site_id'       : file.storage_object_site_id,
                        Property(name="site_id", data_type=DataType.TEXT),
                        # 'site_name'     : sites[file.storage_object_site_id],
                        Property(name="site_name", data_type=DataType.TEXT),
                        # 'size'          : so_attrs.size,
                        Property(name="size", data_type=DataType.INT),
                        # 'created_at'    : so_attrs.created_at,
                        Property(name="created_at", data_type=DataType.DATE),
                        # 'created_by_id' : so_attrs.created_by_id,
                        Property(name="created_at", data_type=DataType.TEXT),
                        # 'updated_at'    : so_attrs.updated_at,
                        Property(name="updated_at", data_type=DataType.DATE),
                        # 'updated_by_id' : so_attrs.updated_by_id,
                        Property(name="updated_by_id", data_type=DataType.TEXT),
                        # 'link'          : make_storage_url(file.storage_version_link),
                        Property(name="link", data_type=DataType.TEXT),
                    ]
                ),

            ],
            vectorizer_config=[
                Configure.NamedVectors.text2vec_ollama(
                    # It's just name
                    name="text_vectorizer",
                    # source_properties: Properties to vectorize
                    source_properties=["data"],     # Text data is here
                    # Ollama API connection string
                    api_endpoint=settings.weaviate_api_endpoint,
                    # Model name. If it's `None`, uses the server-defined default
                    model=settings.weaviate_model,
                )
            ]
        )
        logger.info(f"{msg} done")
    except Exception as e:
        logger.error(f"Failed to create weaviate collection: {e}")


def weaviate_insert(
        client: WeaviateClient,
        texts: list[Document],
        doc_attrs: dict,
        stats: dict,
        index_name: str = settings.weaviate_collection,
):
    """
    Insert multiple documents into weaviate collection.

    We use native create() because we use multiple vector fields.
    Langchain supports only one vector field (property).
    """
    logger.info(msg := f"Inserting {len(texts)} docs into weaviate: {index_name} ...")
    collection: Collection = client.collections.get(index_name)
    with collection.batch.dynamic() as batch:
        for i, text in enumerate(texts, start=1):
            batch.add_object(
                properties={
                    "uuid": str(uuid.uuid4()),
                    "content": text.page_content,
                    "chunk_id": i,
                    **doc_attrs,
                }
            )
        if batch.number_errors > 1:
            logger.error(msg := f"Weaviate batch insert errors: {i}")
            raise AssertionError(msg)
        stats['vectordb']['weaviate_inserted'] = i
        logger.info(f"{msg} done: {i}")
        return i
