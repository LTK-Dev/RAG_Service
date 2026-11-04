from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional, Any, Sequence
from postgres.schemas import DocumentSchema, DocumentStatus
from sqlalchemy.orm import Session


class IDocumentRepository(ABC):

    @abstractmethod
    def get_document_by_id(
        self, session: Session, doc_id: int,
    ) -> DocumentSchema | None:
        raise NotImplementedError()

    @abstractmethod
    def get_documents(
        self,
        session: Session,
        filter_by: Optional[dict[Any, Any]] = None,
        order_by: Optional[Sequence] = None,
        limit: Optional[int] = None,
    ) -> List[DocumentSchema]:
        raise NotImplementedError()

    @abstractmethod
    def create_document(
        self, session: Session, file_name: str, minio_path: str, status: DocumentStatus,
    ) -> DocumentSchema:
        raise NotImplementedError()

    @abstractmethod
    def update_document_status(
        self, session: Session, doc_id: int, status: DocumentStatus,
    ) -> DocumentSchema | None:
        raise NotImplementedError()

    @abstractmethod
    def delete_document(self, session: Session, doc_id: int) -> DocumentSchema | None:
        raise NotImplementedError()
