from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    Text,
    Integer, )
from sqlalchemy.dialects.postgresql import (
    UUID,
    JSONB,
    ARRAY,
    BIGINT,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

from src.models.base import ModelBase

Base = declarative_base()


class StorageObject(ModelBase, Base):
    __tablename__ = 'storage_storageobject'
    __table_args__ = (
        {
            'schema': 'public',
            'info': {'skip_autogenerate': True},  # Skip in alembic migrations
        },
    )
    id                         = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    type                       = Column(Integer, nullable=False)
    name                       = Column(Text, nullable=False)
    description                = Column(String(255), nullable=False)
    deprecated_tags            = Column(ARRAY(String))  # PostgreSQL _varchar array
    size                       = Column(Integer)
    additional                 = Column(JSONB)
    created_at                 = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at                 = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    deleted_at                 = Column(DateTime(timezone=True))
    created_by_id              = Column(Integer, ForeignKey('public.auth_user.id'))
    parent_id                  = Column(UUID(as_uuid=True), ForeignKey('public.storage_storageobject.id'))
    updated_by_id              = Column(Integer, ForeignKey('public.auth_user.id'))
    version_id                 = Column(Integer)  # int8 in PostgreSQL maps to Integer/BigInteger in SQLAlchemy
    object_with_role_id        = Column(UUID(as_uuid=True))
    deleted_by_id              = Column(Integer, ForeignKey('public.auth_user.id'))
    context_folder_id          = Column(UUID(as_uuid=True))
    object_with_extensions_id  = Column(UUID(as_uuid=True))
    site_id                    = Column(UUID(as_uuid=True), ForeignKey('public.sites_site.id'))
    slug                       = Column(String(50))
    file_storage_display_type  = Column(String(100), nullable=False)


class StorageVersion(ModelBase, Base):
    __tablename__ = 'storage_version'
    __table_args__ = (
        {
            'schema': 'public',
            'info': {'skip_autogenerate': True},  # Skip in alembic migrations
        },
    )
    id                 = Column(BIGINT, primary_key=True, autoincrement=True)
    version_number     = Column(Integer, nullable=False)
    size               = Column(Integer)
    comment            = Column(Integer)  # Note: Column name conflicts with SQL keyword
    created_at         = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    link               = Column(String(1024), nullable=False)
    deleted_at         = Column(DateTime(timezone=True))
    storage_object_id  = Column(UUID(as_uuid=True), ForeignKey('public.storage_storageobject.id'))
    created_by_id      = Column(Integer, ForeignKey('public.auth_user.id'))
    deleted_by_id      = Column(Integer, ForeignKey('public.auth_user.id'))
