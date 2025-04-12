import traceback
from typing import Union
from collections.abc import Iterable

from sqlalchemy import create_engine, Row
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Query, Session, sessionmaker
from sqlalchemy.sql import Delete, select

from src.common.log import logger
from src.common.settings import settings
from src.models.cat_meta import SpiderFile
from src.models.vk_filestorage import StorageObject, StorageVersion
from src.models.vk_cms import Site


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


def get_sites(full: bool = True) -> Iterable[Row]:
    with (DbConnManager(settings.vk_db_conn_str_cms) as conn):
        query = select(
            Site.id,
            Site.name,
            Site.created_by_id,
            Site.created_at,
            Site.updated_by_id,
            Site.updated_at,
        )
        if not full:
            query = query.where(
                Site.id.in_(settings.site_ids),
            )
        sites = conn.session.execute(query).all()
        return sites


def get_storage_object(storage_object_id: str) -> StorageObject:
    with (DbConnManager(settings.vk_db_conn_str_filestorage) as conn):
        query = select(
            StorageObject,
            # StorageObject.id,
            # StorageObject.created_at,
            # StorageObject.created_by_id,
            # StorageObject.updated_at,
            # StorageObject.updated_by_id,
        ).where(
            StorageObject.id == storage_object_id,
        )
        result: Row = conn.session.execute(query).fetchone()
        result: StorageObject = result[0]
        return result


def compile_sql(query: Union[type[Query], type[Delete]]):
    if isinstance(query, Query):
        return str(query.statement.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
    else:
        return str(query.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))

