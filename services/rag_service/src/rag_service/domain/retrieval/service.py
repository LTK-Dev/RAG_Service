from __future__ import annotations

import logging
from typing import List
from typing import Optional

from llm import EmbeddingService
from open_search import OpenSearchService
from open_search.schemas import ChunkSchema
from rag_service.shared.exceptions import RetrievalError

logger = logging.getLogger(__name__)


class RetrievalDomainService:
    """Handles the domain logic for context retrieval."""

    def __init__(
        self,
        opensearch_service: OpenSearchService,
        embedding_service: EmbeddingService,
    ):
        self.search = opensearch_service
        self.embed = embedding_service

    def retrieve_context(
        self, question: str, filter_doc_ids: Optional[List[int]],
    ) -> List[ChunkSchema]:
        """Retrieves relevant context chunks for a given question."""
        logger.debug('Domain: Retrieving context for question: %s', question)
        try:
            question_vector = self.embed.get_embeddings([question])[0]
            chunks = self.search.hybrid_search_min_max(
                question_text=question, question_vector=question_vector, k=5,
                filter_doc_ids=filter_doc_ids,
            )
            return chunks
        except Exception:
            logger.exception(
                'Domain: Context retrieval failed',
                extra={
                    'question': question, 'filter_doc_ids': filter_doc_ids,
                },
            )
            raise
