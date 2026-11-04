from __future__ import annotations

import logging
from typing import List
from typing import Optional

from docmanager.domain.getDocument import GetDocumentDomain
from fastapi import Request
from postgres import SQLDatabase
from postgres.schemas import DocumentSchema
from postgres.schemas import DocumentStatus

logger = logging.getLogger(__name__)


class GetDocumentsAppService:
    def __init__(self, request: Request):
        self._request = request

    @property
    def sql_database(self) -> SQLDatabase:
        return self._request.app.state.sql_database

    @property
    def get_domain(self) -> GetDocumentDomain:
        return GetDocumentDomain(sql_database=self.sql_database)

    def get_documents(
        self,
        status: Optional[DocumentStatus],
        order_by: str,
        limit: int,
    ) -> List[DocumentSchema]:
        """Fetches documents from the database."""
        return self.get_domain.get_documents(
            filter_by={'status': status.value} if status else None,
            order_by=[order_by] if order_by else None,
            limit=limit,
        )

    def process(
        self, status: Optional[DocumentStatus], order_by: str, limit: int,
    ) -> List[DocumentSchema]:
        """The single entrypoint for this service."""
        return self.get_documents(
            status=status, order_by=order_by, limit=limit,
        )
