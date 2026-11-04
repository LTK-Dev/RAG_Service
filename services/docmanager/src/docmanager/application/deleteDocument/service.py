from __future__ import annotations

import logging

from docmanager.domain.deleteDocument import DeleteDocumentDomain
from docmanager.shared.settings import Settings
from fastapi import Request
from open_search import OpenSearchService
from postgres import SQLDatabase
from storage import MinioService

logger = logging.getLogger(__name__)


class DeleteDocumentAppService:
    def __init__(self, request: Request):
        """
        Initializes the App Service by receiving the request object.
        """
        self._request = request

    @property
    def sql_database(self) -> SQLDatabase:
        """Gets the SQLDatabase client from app state."""
        return self._request.app.state.sql_database

    @property
    def minio_service(self) -> MinioService:
        """Gets the MinioService client from app state."""
        return self._request.app.state.minio_service

    @property
    def opensearch_service(self) -> OpenSearchService:
        """Gets the OpenSearchService client from app state."""
        return self._request.app.state.opensearch_service

    @property
    def settings(self) -> Settings:
        """Gets the service settings from app state."""
        return self._request.app.state.settings

    @property
    def delete_domain(self) -> DeleteDocumentDomain:
        """Initializes the Domain Service."""
        return DeleteDocumentDomain(
            sql_database=self.sql_database,
            minio_service=self.minio_service,
            opensearch_service=self.opensearch_service,
            minio_bucket=self.settings.minio.bucket,
        )

    def process(self, doc_id: int) -> None:
        """The single entrypoint for this service."""
        self.delete_domain.delete_document_by_id(doc_id)
