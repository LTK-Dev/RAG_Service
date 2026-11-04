import logging
from contextlib import contextmanager
from typing import List, Any, Dict, Iterator
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
from postgres.controller import DocumentController
from postgres.schemas import DocumentSchema

logger = logging.getLogger(__name__)


class SQLDatabase(DocumentController):
    def __init__(self, dsn: str):
        self.conn_string = dsn
        if not self.conn_string:
            # Lỗi sập hệ thống
            logger.critical(
                'CRITICAL: POSTGRES_DSN (Connection String) was not provided.',
            )
            raise ValueError('DSN was not provided.')

        try:
            logger.info('Initializing SQLAlchemy Engine...')
            self.engine = create_engine(dsn, pool_pre_ping=True)
            self.SessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=self.engine,
            )
            super().__init__()
            logger.info('SQLAlchemy Engine and Repositories are ready.')
        except Exception as e:
            # Lỗi sập hệ thống
            logger.critical(
                f"CRITICAL: Failed to initialize SQLAlchemy Engine: {e}", exc_info=True,
            )
            raise

    @contextmanager
    def get_session(self) -> Iterator[Session]:
        session: Session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            # Lỗi thao tác
            logger.exception(f"DB Session/Transaction Error, rolling back: {e}")
            session.rollback()
            raise
        finally:
            session.close()

    def close_engine(self):
        if self.engine:
            logger.info('Closing SQLAlchemy Engine connections...')
            self.engine.dispose()
