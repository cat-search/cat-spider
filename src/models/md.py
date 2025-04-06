from datetime import datetime, UTC

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
    Integer,
)
from sqlalchemy.dialects.postgresql import UUID, VARCHAR, BIGINT, SMALLINT, TIMESTAMP
from sqlalchemy.sql import func, select, Select, desc
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from src.common.db import DbConnManager

Base = declarative_base()


class Checkpoint(Base):
    __tablename__ = 't_checkpoint'
    __table_args__ = (
        {
            'schema': 'md',
        },
    )

    id = Column(BIGINT, primary_key=True)
    ts = Column(TIMESTAMP, default=datetime.now(UTC))

    @classmethod
    def log(cls, conn):
        return conn.persist_add(cls())

    @classmethod
    def get_last(cls, conn: DbConnManager) -> datetime:
        query = select(cls.ts).order_by(desc(cls.id)).limit(1)
        ts = conn.session.scalar(query)

        return ts if ts else datetime.fromtimestamp(0)
