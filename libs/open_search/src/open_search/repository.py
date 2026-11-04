from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional
from .schemas import ChunkSchema


class IOpenSearchRepository(ABC):
    @abstractmethod
    def index_chunks(self, chunks: List[ChunkSchema]) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def delete_chunks_by_doc_id(self, doc_id: int) -> dict:
        raise NotImplementedError()

    @abstractmethod
    def hybrid_search_min_max(
        self,
        question_text: str,
        question_vector: List[float],
        k: int,
        filter_doc_ids: Optional[List[int]] = None,
    ) -> List[ChunkSchema]:
        raise NotImplementedError()
