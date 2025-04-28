import time
import uuid

from langchain_core.documents import Document
from weaviate import WeaviateClient
from weaviate import connect_to_local as weaviate_connect_to_local
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.init import Auth
from weaviate.collections import Collection
from weaviate.collections.classes.config import Tokenization

from src.common.log import logger
from src.common.settings import settings


def init_weaviate() -> WeaviateClient:
    """ Инициализация подключения """
    logger.info(
        msg := f"Initializing weaviate client: {settings.weaviate_host}:{settings.weaviate_port} ..."
    )
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
    logger.info(f"{msg} done")
    return client


def delete_collection(
        client: WeaviateClient, collection_name: str = settings.weaviate_collection,
):
    if not client.collections.exists(collection_name):
        logger.info(f"Collection {collection_name} doesnt exists")
        return

    logger.info(msg := f"Deleting collection: {collection_name} ...")
    client.collections.delete(collection_name)
    logger.info(f"{msg} done: OK")


def create_collection(
        client: WeaviateClient, collection_name: str = settings.weaviate_collection,
) -> None:
    """
    Create a collection in weaviate if it doesn't exist

    We use native create() because we use multiple vector fields.
    """
    logger.info(msg := f"Creating weaviate collection: {collection_name} ...")

    # Check if collection exists in weaviate
    if client.collections.exists(collection_name):
        logger.info(f"Collection {collection_name} already exists")
        return

    logger.info(
        f"Collection params:"
        f"\nname: {collection_name}"
        f"\napi endpoint: {settings.weaviate_api_endpoint}"
        f"\nmodel: {settings.weaviate_model}"
    )
    try:
        collection: Collection = client.collections.create(
            collection_name,
            properties=[
                # Property tokenization: The tokenization method to use for
                # the inverted index. Defaults to `None`.
                #
                # content: chunk of text
                Property(name="content", data_type=DataType.TEXT, tokenization=Tokenization.WORD),
                # Name, title
                Property(name="name", data_type=DataType.TEXT, tokenization=Tokenization.FIELD),
                # Type: site, page, file, list
                Property(name="type", data_type=DataType.TEXT, tokenization=Tokenization.FIELD),
                # Object id (site id, page id, file id, list id)
                Property(name="object_id", data_type=DataType.UUID),
                # Page number
                Property(name="page", data_type=DataType.INT),
                # Chunk number
                Property(name="chunk_id", data_type=DataType.INT),
                # 'site_id'       : file.storage_object_site_id,
                Property(name="site_id", data_type=DataType.TEXT, tokenization=Tokenization.FIELD),
                # 'site_name'     : sites[file.storage_object_site_id],
                Property(name="site_name", data_type=DataType.TEXT, tokenization=Tokenization.WORD),
                # 'size'          : so_attrs.size,
                Property(name="size", data_type=DataType.INT),
                # 'created_at'    : so_attrs.created_at,
                Property(name="created_at", data_type=DataType.DATE),
                # 'created_by_id' : so_attrs.created_by_id,
                Property(name="created_by_id", data_type=DataType.TEXT, tokenization=Tokenization.FIELD),
                # 'updated_at'    : so_attrs.updated_at,
                Property(name="updated_at", data_type=DataType.DATE),
                # 'updated_by_id' : so_attrs.updated_by_id,
                Property(name="updated_by_id", data_type=DataType.TEXT, tokenization=Tokenization.FIELD),
                # 'link'          : make_storage_url(file.storage_version_link),
                Property(name="link", data_type=DataType.TEXT, tokenization=Tokenization.FIELD),
            ],
            vectorizer_config=[
                # Configure.NamedVectors.text2vec_huggingface()  # TODO: Test models from wiki
                Configure.NamedVectors.text2vec_ollama(
                    # It's just name
                    name="text_vectorizer",
                    # source_properties: Properties to vectorize
                    source_properties=["content"],  # It has to match the field name
                    # Ollama API connection string
                    api_endpoint=settings.weaviate_api_endpoint,
                    # Model name. If it's `None`, uses the server-defined default
                    model=settings.weaviate_model,
                ),
            ],
            # inverted_index_config=
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
        file_name: str = None,
):
    """
    Insert multiple documents into weaviate collection.

    We use native create() because we use multiple vector fields.
    Langchain supports only one vector field (property).
    """
    logger.info(msg := f"Inserting {len(texts)} docs into weaviate: {index_name} ...")
    collection: Collection = client.collections.get(index_name)
    i = 0
    with collection.batch.dynamic() as batch:
        for i, text in enumerate(texts, start=1):
            batch.add_object(
                properties={
                    "content": text.page_content,
                    "chunk_id": i,
                    **doc_attrs,
                }
            )

            # Chunk statistics calculation
            chunk_len = (len(text.page_content) // 50) * 50
            stats['vectordb']['chunk'][chunk_len] += 1
            if chunk_len < 100:
                stats['file'][file_name]['chunk_len<100'] += 1
            elif chunk_len > 1000:
                stats['file'][file_name]['chunk_len>1000'] += 1

        if batch.number_errors > 1:
            logger.error(msg := f"Weaviate batch insert errors: {batch.number_errors}")
            raise AssertionError(msg)
        stats['vectordb']['weaviate_inserted'] += i
        logger.info(f"{msg} done: {i}")
        return i


def weaviate_insert_plain(
        client: WeaviateClient,
        texts: list[str],
        doc_attrs: dict,
        stats: dict,
        index_name: str = settings.weaviate_collection,
        object_name: str = None,
):
    """
    Insert multiple documents into weaviate collection.
    """
    logger.info(msg := f"Inserting {len(texts)} docs into weaviate: {index_name} ...")
    collection: Collection = client.collections.get(index_name)
    inserted_count: int = 0  # Inserted
    min_size: int = settings.text_chunk_min_size
    with collection.batch.dynamic() as batch:
        for i, text in enumerate(texts, start=1):
            # Chunk statistics calculation
            chunk_len = (len(text) // 50) * 50
            stats['vectordb']['chunk'][chunk_len] += 1
            if chunk_len < min_size:
                stats['source_object'][object_name][f'chunk_len<{min_size}'] += 1
            elif chunk_len > 1000:
                stats['source_object'][object_name]['chunk_len>1000'] += 1

            # Insert
            if len(text) >= min_size:
                batch.add_object(
                    properties={
                        "content": text,
                        "chunk_id": i,
                        **doc_attrs,
                    }
                )
                inserted_count += 1
                stats['vectordb']['weaviate_inserted'] += 1
                stats['vectordb']['weaviate_inserted_size'] += len(text)
            else:
                stats['vectordb']['weaviate_skipped'] += 1
                stats['vectordb']['weaviate_skipped_size'] += len(text)
                continue

        if batch.number_errors > 1:
            logger.error(msg := f"Weaviate batch insert errors: {batch.number_errors}")
            raise AssertionError(msg)

        logger.info(f"{msg} done: {i}")
        return inserted_count


def check_collection_readiness(
        client: WeaviateClient, index_name: str = settings.weaviate_collection
):
    new_uuid = str(uuid.uuid4())
    doc_attrs = {
        # '_id'               : f"{file.storage_object_id}",
        'object_id'     : new_uuid,
        'type'          : None,
        'name'          : None,
        'site_id'       : None,
        'site_name'     : None,
        'size'          : None,
        'created_at'    : None,
        'created_by_id' : None,
        'updated_at'    : None,
        'updated_by_id' : None,
        'link'          : None,
    }
    logger.info(msg := f"Checking if we able to insert into: {index_name} ...")
    collection: Collection = client.collections.get(index_name)
    properties = {
        "uuid": new_uuid,
        "content": "test",
        "chunk_id": 1,
        **doc_attrs,
    }

    while True:
        msg = ""
        try:
            # Check insert
            res_uuid = collection.data.insert(properties=properties)
            # Check query by uuid
            document = collection.query.fetch_object_by_id(res_uuid)
            if document is not None:
                break
        except Exception as e:  # We will fall here when ollama model hasn't pulled
            msg = str(e)
            pass
        logger.error(f"Failed to insert: {msg}. Sleeping ...")
        time.sleep(10)

    collection.data.delete_by_id(res_uuid)
    logger.info(f"{msg} done: OK")

