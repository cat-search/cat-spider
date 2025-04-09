import traceback
from typing import Union

from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Query
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.sql import Delete

from src.common.log import logger
from src.models.cat_meta import SpiderFile
from src.models.vk_filestorage import StorageObject, StorageVersion


class DbConnManager:
    def __init__(self, conn_str, echo=False):
        self.conn_str = conn_str
        self.echo = echo

        self._logger = logger

    def __enter__(self):
        self.engine = create_engine(self.conn_str, echo=self.echo)
        session_factory = sessionmaker(bind=self.engine)
        self.session: Session = session_factory()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_tb:
            traceback.print_tb(exc_tb)
        self.session.close()

    def __getattr__(self, item):
        return getattr(self.session, item)

    def commit(self):
        try:
            self.session.commit()
        except Exception as e:
            self.rollback()
            raise e

    def rollback(self):
        self.session.rollback()


def file_register(
        conn: DbConnManager,
        data: StorageObject | StorageVersion,
        filename: str,
        status_id: int
) -> None:
    with DbConnManager(conn.conn_str) as conn:
        # StorageObject.id,
        # StorageObject.name,                # filename
        # StorageObject.context_folder_id,   # папка, определяющая контекст (например, Blog_{id}).
        # StorageObject.created_at,
        # StorageObject.created_by_id,
        # StorageObject.updated_at,
        # StorageObject.updated_by_id,
        # StorageObject.site_id,
        # StorageVersion.size,                # file size
        # StorageVersion.link,                # download link
        conn.session.add(
            SpiderFile(
                storage_object_id=data.id,
                storage_object_name=data.name,
                storage_object_site_id=data.site_id,
                storage_version_size=data.size,
                storage_version_link=data.link,
                target_path=filename,
                status_id=status_id,
            )
        )
        conn.commit()


def file_set_status(conn: DbConnManager, file_id: str, status_id: int) -> None:
    with DbConnManager(conn.conn_str) as conn:
        conn.session.query(SpiderFile).filter(SpiderFile.storage_object_id == file_id).update(
            {SpiderFile.status_id: status_id}
        )
        conn.commit()


