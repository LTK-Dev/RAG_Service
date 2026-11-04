from __future__ import annotations

import logging
from typing import List
from typing import Optional

from fastapi import Request
from llm import EmbeddingService
from llm import LLMService
from open_search import OpenSearchService
from rag_service.api.schemas import (
    ContextChunkResponse,
    RAGResponse,
)
from rag_service.domain.generation import GenerationDomainService
from rag_service.domain.retrieval import RetrievalDomainService

logger = logging.getLogger(__name__)


class RAGAppService:
    def __init__(self, request: Request):
        self._request = request

    @property
    def opensearch_service(self) -> OpenSearchService:
        """Gets the OpenSearchService client from app state."""
        return self._request.app.state.opensearch_service

    @property
    def llm_service(self) -> LLMService:
        """Gets the LLMService client from app state."""
        return self._request.app.state.llm_service

    @property
    def embedding_service(self) -> EmbeddingService:
        """Gets the EmbeddingService client from app state."""
        return self._request.app.state.embedding_service

    @property
    def retrieval_domain(self) -> RetrievalDomainService:
        """Initializes the Retrieval Domain Service."""
        return RetrievalDomainService(
            opensearch_service=self.opensearch_service,
            embedding_service=self.embedding_service,
        )

    @property
    def generation_domain(self) -> GenerationDomainService:
        """Initializes the Generation Domain Service."""
        return GenerationDomainService(llm_service=self.llm_service)

    def process(
        self, question: str, filter_doc_ids: Optional[List[int]],
    ) -> RAGResponse:
        """The single entrypoint for the RAG service."""
        logger.debug('Application: Handling RAG request for: %s', question)

        context_chunks = self.retrieval_domain.retrieve_context(
            question=question, filter_doc_ids=filter_doc_ids,
        )
        answer = self.generation_domain.generate_answer(
            question=question, chunks=context_chunks,
        )

        context_response = [
            ContextChunkResponse(doc_id=chunk.doc_id, text_chunk=chunk.text_chunk)
            for chunk in context_chunks
        ]

        return RAGResponse(
            answer=answer, context=context_response,
        )
