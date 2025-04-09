from datetime import datetime, UTC
from enum import Enum

from sqlalchemy import (
    Column,
)
from sqlalchemy.dialects.postgresql import (
    UUID, VARCHAR, SMALLINT, TIMESTAMP, TEXT,
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class SpiderFile(Base):
    """ Учет файлов из хранилища """
    __tablename__ = 'spider_file'
    __table_args__ = (
        {
            'schema': 'meta',
        },
    )
    storage_object_id        = Column(UUID, primary_key=True, comment='filestorage.storage_object.id')
    storage_object_name      = Column(TEXT, comment='filestorage.storage_object.name')
    storage_object_site_id   = Column(TEXT, comment='filestorage.storage_object.site_id')
    storage_version_size     = Column(TEXT, comment='filestorage.storage_version.size')
    storage_version_link     = Column(TEXT, comment='filestorage.storage_version.link')

    create_ts                = Column(TIMESTAMP, default=datetime.now(UTC))
    target_path              = Column(VARCHAR(1024), comment='file path')
    status_id                = Column(SMALLINT, default=0, comment='0 - new, 1 - downloaded, 2 - parsed, 3 - vectorized')


class Status(str, Enum):
    """ Статусы файлов """
    new         = 0
    downloaded  = 1
    parsed      = 2
    done        = 3
    error       = 4


# class Checkpoint(Base):
#     __tablename__ = 't_checkpoint'
#     __table_args__ = (
#         {
#             'schema': 'meta',
#         },
#     )
#
#     id = Column(BIGINT, primary_key=True)
#     ts = Column(TIMESTAMP, default=datetime.now(UTC))
#
#     @classmethod
#     def log(cls, conn):
#         return conn.persist_add(cls())
#
#     @classmethod
#     def get_last(cls, conn: DbConnManager) -> datetime:
#         query = select(cls.ts).order_by(desc(cls.id)).limit(1)
#         ts = conn.session.scalar(query)
#
#         return ts if ts else datetime.fromtimestamp(0)
