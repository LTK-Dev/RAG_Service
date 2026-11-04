from __future__ import annotations

import logging
from io import BytesIO

from docmanager.domain.indexingDocument import IndexingDomainService
from docmanager.shared.settings import Settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from llm import EmbeddingService
from open_search import OpenSearchService
from parser import DocxParser
from parser import PdfParser
from postgres import SQLDatabase
from postgres.schemas import DocumentStatus
from storage import MinioService

logger = logging.getLogger(__name__)


class IndexingAppService:

    _domain_service: IndexingDomainService | None = None

    def __init__(
        self,
        settings: Settings,
        db: SQLDatabase,
        storage: MinioService,
        search: OpenSearchService,
        embed: EmbeddingService,
    ):
        """
        Initializes the App Service with injected clients.
        """
        self.db = db
        self.storage = storage
        self.minio_bucket = settings.minio.bucket
        self.parsers = {
            'application/pdf': PdfParser(),
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document':  # noqa: E501
                DocxParser(),
        }
        # Khởi tạo bộ cắt (Splitter) - Chiến thuật Chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=100,  # Gối đầu 100 ký tự
        )

        self._domain_service = IndexingDomainService(
            sql_database=self.db,
            opensearch_service=search,
            embedding_service=embed,
        )

    def run_indexing_task(self, doc_id: int, minio_path: str, content_type: str):
        """
        Hàm sẽ được chạy trong BackgroundTasks.
        """
        logger.info(
            'Background task started for doc_id: %s', doc_id,
        )
        if self._domain_service is None:
            raise RuntimeError('IndexingDomainService was not initialized')
        try:
            # (Logic chạy trong 1 thread riêng)
            # Cập nhật Status (PROCESSING)
            with self.db.get_session() as session:
                self.db.update_document_status(
                    session, doc_id,
                    DocumentStatus.PROCESSING,
                )

            # Lấy file từ Minio
            file_data: BytesIO = self.storage.get_file(
                self.minio_bucket, minio_path,
            )

            # Parse - Dùng Strategy Pattern
            parser = self.parsers.get(content_type)
            if not parser:
                raise ValueError(
                    f"No parser found for content type {content_type}",
                )
            text = parser.parse(file_data)

            # Chunking (Cắt nhỏ) - Dùng LangChain
            chunks_str = self.text_splitter.split_text(text)

            # Gọi Domain Service để thực hiện nghiệp vụ lõi
            self._domain_service.index_document_chunks(
                doc_id=doc_id, text_chunks=chunks_str,
            )

            # Cập nhật Status (COMPLETED)
            with self.db.get_session() as session:
                self.db.update_document_status(
                    session, doc_id,
                    DocumentStatus.COMPLETED,
                )
            logger.info(
                'Application: Successfully processed and indexed document ID %s.',
                doc_id,
            )

        except Exception:
            logger.exception(
                'Background task FAILED for doc_id: %s', doc_id,
            )
            # Cập nhật status FAILED
            with self.db.get_session() as session:
                self.db.update_document_status(
                    session, doc_id, DocumentStatus.FAILED,
                )
