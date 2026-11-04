from __future__ import annotations

import logging

from docmanager.application.indexingDocument import IndexingAppService
from docmanager.domain.createDocument import CreateDocumentDomain
from docmanager.shared.settings import Settings
from fastapi import BackgroundTasks
from fastapi import Request
from fastapi import UploadFile
from postgres import SQLDatabase
from postgres.schemas import DocumentSchema
from storage import MinioService
# Import Application Service
# Import Domain Service

logger = logging.getLogger(__name__)


class CreateDocumentAppService:
    def __init__(self, request: Request):
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
    def settings(self) -> Settings:
        """Gets the service settings from app state."""
        return self._request.app.state.settings

    @property
    def create_domain(self) -> CreateDocumentDomain:
        """Initializes the Domain Service."""
        return CreateDocumentDomain(
            sql_database=self.sql_database,
            minio_service=self.minio_service,
            bucket_name=self.settings.minio.bucket,
        )

    @property
    def indexing_service(self) -> IndexingAppService:
        """Initializes the Indexing Application Service."""
        return IndexingAppService(
            settings=self.settings,
            db=self.sql_database,
            storage=self.minio_service,
            search=self._request.app.state.opensearch_service,
            embed=self._request.app.state.embedding_service,
        )

    # --- Hàm Business Logic ---

    def create_document(self, upload_file: UploadFile) -> DocumentSchema:
        """
        Reads file bytes and passes them to the domain layer.
        """
        logger.debug(
            f"Application layer: Handling file {upload_file.filename}",
        )
        file_content = upload_file.file.read()

        return self.create_domain.create_document(
            file_bytes=file_content,
            file_name=upload_file.filename,
            content_type=upload_file.content_type,
        )

    def create_document_and_queue_indexing(
        self, upload_file: UploadFile, background_tasks: BackgroundTasks,
    ) -> DocumentSchema:
        """
        Orchestrates creating a document and queueing it for indexing.
        """
        # Create document entry in DB and upload to Minio
        new_document = self.create_document(upload_file)

        # Add indexing task to background queue
        logger.info(
            f"Queueing background indexing task for doc_id: {new_document.id}",
        )
        background_tasks.add_task(
            self.indexing_service.run_indexing_task,
            doc_id=new_document.id,
            minio_path=new_document.minio_path,
            content_type=upload_file.content_type,
        )

        return new_document

    def process(
        self, upload_file: UploadFile, background_tasks: BackgroundTasks,
    ) -> DocumentSchema:
        """
        The single entrypoint for this service.
        It handles the creation and queuing of a document for indexing.
        """
        return self.create_document_and_queue_indexing(
            upload_file=upload_file,
            background_tasks=background_tasks,
        )
