import logging
from typing import List, Optional
from io import BytesIO
import uuid

from postgres.schemas import DocumentSchema, DocumentStatus
from storage import MinioInput, MinioService
from postgres import SQLDatabase
from docmanager.shared.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class CreateDocumentDomain:
    def __init__(
        self, sql_database: SQLDatabase, minio_service: MinioService, bucket_name: str,
    ):
        """
        Initializes the domain service with necessary clients.
        """
        self.db = sql_database
        self.storage = minio_service
        self.bucket_name = bucket_name

    def create_document(
        self, file_bytes: bytes, file_name: str, content_type: str,
    ) -> DocumentSchema:
        """
        Raw domain logic for creating a new document entry.
        """
        logger.debug('Domain layer: Uploading to Minio and creating DB record...')

        try:
            object_name = f"{uuid.uuid4()}-{file_name}"  # Tạo tên file duy nhất

            minio_input = MinioInput(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=BytesIO(file_bytes),
                content_type=content_type,
            )
            self.storage.upload_file(input=minio_input)

            # Logic tạo bản ghi DB
            with self.db.get_session() as session:
                new_document = self.db.create_document(
                    session=session,
                    file_name=file_name,
                    minio_path=object_name,
                    status=DocumentStatus.PENDING,
                )

            return new_document

        except Exception as e:
            logger.exception(
                'Domain layer: Error creating document', extra={'file_name': file_name},
            )
            raise DatabaseError(f"Error in domain layer: {e}")
