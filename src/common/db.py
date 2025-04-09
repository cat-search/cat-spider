import traceback
from typing import Union

from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Query
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.sql import Delete

from src.common.log import logger


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
