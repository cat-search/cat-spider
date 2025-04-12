from bson.binary import UuidRepresentation
from bson.codec_options import CodecOptions
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError
from pymongo.results import InsertOneResult

from src.common.settings import settings
from src.common.log import logger


def init_mongo(collection: str) -> Collection:
    """
    Initialize MongoDB client, db, collection
    """
    client = MongoClient(
        host=settings.mongo_host,
        port=settings.mongo_port,
    )
    db = client.get_database(settings.mongo_db_name)
    python_opts = CodecOptions(uuid_representation=UuidRepresentation.PYTHON_LEGACY)
    coll = db.get_collection(
        collection,
        codec_options=python_opts,
    )
    return coll


def mongo_insert(coll: Collection, doc: dict, stats: dict):
    try:
        result: InsertOneResult = coll.insert_one(doc)  # Insert document into MongoDB
        stats['mongo']['inserted'] += 1
    except DuplicateKeyError:  # Duplicated _id (site_id) in MongoDB
        stats['mongo']['duplicate_key_error'] += 1
    except Exception as e:
        logger.error(f"Failed insert into mongo: {e}")
