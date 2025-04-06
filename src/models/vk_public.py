from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from src.models.base import ModelBase

Base = declarative_base()


class Site(ModelBase, Base):
    __tablename__ = 'sites_site'
    __table_args__ = (
        {
            'schema': 'public',
            'info': {'skip_autogenerate': True},  # Skip in alembic migrations
        },
    )

    id                          = Column(UUID(as_uuid=True), primary_key=True)
    name                        = Column(String(150), nullable=False)
    description                 = Column(String(1500), nullable=False)
    slug                        = Column(String(50), nullable=False)
    status                      = Column(String(20), nullable=False)
    is_navigation_visible       = Column(Boolean, nullable=False)
    created_at                  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at                  = Column(DateTime(timezone=True), onupdate=func.now())

    # Foreign keys
    filestorage_root_folder_id  = Column(UUID(as_uuid=True))
    parent_id                   = Column(UUID(as_uuid=True))
    created_by_id               = Column(UUID(as_uuid=True))
    updated_by_id               = Column(UUID(as_uuid=True))

    # Relationships
    # parent                      = relationship('Site', remote_side=[id])
    # created_by                  = relationship('User', foreign_keys=[created_by_id])
    # updated_by                  = relationship('User', foreign_keys=[updated_by_id])

