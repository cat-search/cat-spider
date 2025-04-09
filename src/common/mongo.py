from bson.binary import UuidRepresentation
from bson.codec_options import CodecOptions
from pymongo import MongoClient
from pymongo.collection import Collection

from src.common.settings import settings


def init_mongo(collection: str) -> Collection:
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
