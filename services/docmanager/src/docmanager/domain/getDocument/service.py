import logging
from typing import List, Optional, Tuple, Any
from postgres.schemas import DocumentSchema
from postgres.client import SQLDatabase
from docmanager.shared.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class GetDocumentDomain:
    def __init__(self, sql_database: SQLDatabase):
        self.db = sql_database

    def get_documents(
        self,
        filter_by: Optional[dict[Any, Any]],
        order_by: Optional[List[str]],
        limit: Optional[int],
    ) -> List[DocumentSchema]:

        logger.debug('Domain layer: Calling repository...')
        try:
            with self.db.get_session() as session:
                return self.db.get_documents(
                    session=session, filter_by=filter_by, order_by=order_by, limit=limit,
                )
        except Exception as e:
            logger.exception(
                'Domain layer: Error calling repository', extra={'filter': filter_by},
            )
            raise DatabaseError(f"Error in domain layer: {e}")
