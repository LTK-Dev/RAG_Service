# libs/postgres/src/postgres/controller/document_controller.py
from __future__ import annotations

import logging
from typing import Any
from typing import cast
from typing import List
from typing import Optional
from typing import Sequence

from postgres.models import DocumentModel
from postgres.repository import IDocumentRepository
from postgres.schemas import DocumentSchema
from postgres.schemas import DocumentStatus
from sqlalchemy import asc
from sqlalchemy import delete
from sqlalchemy import desc
from sqlalchemy import insert
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class DocumentController(IDocumentRepository):

    def __init__(self):
        pass

    def get_documents(
        self,
        session: Session,
        filter_by: Optional[dict[Any, Any]] = None,
        order_by: Optional[Sequence] = None,
        limit: Optional[int] = None,
    ) -> List[DocumentSchema]:
        """Retrieves documents with optional filtering, sorting, and pagination.
        Args:
            session (Session): The SQLAlchemy database session.
            filter_by (Optional[dict[Any, Any]]): Fields to filter by.
            order_by (Optional[Sequence]): Fields to order by. Supports
                "field:asc" or "field:desc".
            limit (Optional[int]): Max number of documents.

        Returns:
            List[DocumentSchema]: A list of matching document schemas.

        Raises:
            Exception: If a database error occurs during query execution.
        """

        logger.debug('Repository: Fetching documents...')
        stmt = select(DocumentModel)

        if filter_by:
            stmt = stmt.filter_by(**filter_by)

        if order_by is not None:
            for ob_str in order_by:
                if ':' in ob_str:
                    field, direction = ob_str.split(':')
                    if hasattr(DocumentModel, field):
                        col = getattr(DocumentModel, field)
                        stmt = stmt.order_by(
                            desc(col) if direction == 'desc' else asc(col),
                        )
                elif hasattr(DocumentModel, ob_str):
                    stmt = stmt.order_by(asc(getattr(DocumentModel, ob_str)))

        if limit is not None:
            stmt = stmt.limit(limit)

        try:
            results = session.scalars(stmt).all()
            documents = [DocumentSchema.model_validate(doc) for doc in results]
            logger.info(f"Repository: Found {len(documents)} document(s).")
            return cast(List[DocumentSchema], documents)

        except Exception as e:
            logger.exception(
                'Repository: SQLAlchemy error fetching documents',
                extra={
                    'filter': filter_by,
                    'order_by': order_by,
                },
            )
            raise e

    def create_document(
        self, session: Session, file_name: str, minio_path: str, status: DocumentStatus,
    ) -> DocumentSchema:
        """
        Creates a new document record in the database.

        Args:
            session (Session): The SQLAlchemy database session.
            file_name (str): The original name of the file.
            minio_path (str): The path/object_name of the file in Minio.
            status (DocumentStatus): The initial status (e.g., PENDING).

        Returns:
            DocumentSchema: The Pydantic schema of the newly created document.
        """

        logger.debug('Repository: Creating new document record...')
        try:
            # The 'returning' clause requires this statement composition
            # for SQLAlchemy to process it correctly.
            stmt = (
                insert(DocumentModel)
                .values(
                    file_name=file_name, minio_path=minio_path,
                    status=status.value,
                )
                .returning(DocumentModel)  # Yêu cầu trả về bản ghi đã tạo
            )

            new_doc_model = session.scalar(stmt)

            if not new_doc_model:
                raise Exception(
                    'Failed to create document (no row returned).',
                )

            logger.info(
                'Repository: Created document record with ID %s.',
                new_doc_model.id,
            )
            return DocumentSchema.model_validate(new_doc_model)

        except Exception as e:
            logger.exception(
                'Repository: SQLAlchemy error creating document',
                extra={'file_name': file_name},
            )
            raise e

    def update_document_status(
        self, session: Session, doc_id: int, status: DocumentStatus,
    ) -> DocumentSchema | None:
        """
        Updates the status of a specific document.

        Args:
            session (Session): The SQLAlchemy database session.
            doc_id (int): The ID of the document to update.
            status (DocumentStatus): The new status for the document.

        Returns:
            DocumentSchema | None: The updated document schema if found, otherwise None.
        """

        logger.debug(
            'Repository: Updating status for doc_id %s to %s',
            doc_id, status.value,
        )
        try:
            stmt = (
                update(DocumentModel)
                .where(DocumentModel.id == doc_id)
                .values(status=status.value)
                .returning(DocumentModel)
            )

            updated_doc_model = session.scalar(stmt)

            if not updated_doc_model:
                logger.warning(
                    'Repository: No document found with ID %s to update.',
                    doc_id,
                )
                return None

            return DocumentSchema.model_validate(updated_doc_model)

        except Exception as e:
            logger.exception(
                'Repository: SQLAlchemy error updating document status',
                extra={'doc_id': doc_id},
            )
            raise e

    def delete_document(self, session: Session, doc_id: int) -> DocumentSchema | None:
        """
        Deletes a document record from the database by its ID.
        """
        logger.debug(
            'Repository: Deleting document record for doc_id %s...', doc_id,
        )
        try:

            stmt = (
                delete(DocumentModel)
                .where(DocumentModel.id == doc_id)
                .returning(DocumentModel)
            )

            deleted_doc_model = session.scalar(stmt)

            if not deleted_doc_model:
                logger.warning(
                    'Repository: No document found with ID %s to delete.', doc_id,
                )
                return None

            logger.info(
                'Repository: Deleted document record with ID %s.', doc_id,
            )
            return DocumentSchema.model_validate(deleted_doc_model)

        except Exception as e:
            logger.exception(
                'Repository: SQLAlchemy error deleting document',
                extra={'doc_id': doc_id},
            )
            raise e

    def get_document_by_id(
        self, session: Session, doc_id: int,
    ) -> DocumentSchema | None:
        """
        Fetches a single document from the database by its ID.
        """
        logger.debug('Repository: Fetching document with ID: %s', doc_id)
        try:

            stmt = select(DocumentModel).where(DocumentModel.id == doc_id)

            doc_model = session.scalar(stmt)

            if not doc_model:
                logger.warning(
                    'Repository: No document found with ID %s.', doc_id,
                )
                return None

            logger.info('Repository: Found document with ID %s.', doc_id)
            return DocumentSchema.model_validate(doc_model)

        except Exception as e:
            logger.exception(
                'Repository: SQLAlchemy error fetching document by ID',
                extra={'doc_id': doc_id},
            )
            raise e
