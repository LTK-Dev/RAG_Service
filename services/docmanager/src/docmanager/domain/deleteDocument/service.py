import logging
from postgres import SQLDatabase
from storage import MinioService
from open_search import OpenSearchService
from storage import MinioInput
from docmanager.shared.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class DeleteDocumentDomain:
    def __init__(
        self,
        sql_database: SQLDatabase,
        minio_service: MinioService,
        opensearch_service: OpenSearchService,
        minio_bucket: str,
    ):
        self.db = sql_database
        self.storage = minio_service
        self.search = opensearch_service
        self.bucket_name = minio_bucket

    def delete_document_by_id(self, doc_id: int):
        """
        Domain logic to completely delete a document from all systems.
        """
        logger.debug(f"Domain: Deleting document ID {doc_id}...")

        try:
            # Lấy thông tin (minio_path) TỪ POSTGRES TRƯỚC KHI XÓA
            with self.db.get_session() as session:
                doc = self.db.get_document_by_id(session=session, doc_id=doc_id)

            if not doc:
                logger.warning(
                    f"Domain: Document ID {doc_id} not found. Nothing to delete.",
                )
                return

            minio_path = doc.minio_path

            # Xóa khỏi OpenSearch
            logger.debug(
                f"Domain: Deleting chunks for doc_id {doc_id} from OpenSearch...",
            )
            self.search.delete_chunks_by_doc_id(doc_id=doc_id)

            # Xóa khỏi Minio
            logger.debug(f"Domain: Deleting file {minio_path} from Minio...")
            minio_input = MinioInput(
                bucket_name=self.bucket_name, object_name=minio_path,
            )
            self.storage.delete_file(input=minio_input)

            # Xóa khỏi Postgres
            logger.debug(
                f"Domain: Deleting record for doc_id {doc_id} from Postgres...",
            )
            with self.db.get_session() as session:
                self.db.delete_document(session=session, doc_id=doc_id)

            logger.info(f"Domain: Successfully deleted document ID {doc_id}.")

        except Exception as e:
            logger.exception(
                f"Domain: Failed to delete document ID {doc_id}",
                extra={'doc_id': doc_id},
            )
            raise DatabaseError(f"Error in domain layer: {e}")
