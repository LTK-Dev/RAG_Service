from __future__ import annotations

import logging
from typing import List

from llm import LLMService
from open_search.schemas import ChunkSchema
from rag_service.shared.exceptions import GenerationError
from .prompts import RAG_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


class GenerationDomainService:
    """Handles the domain logic for answer generation."""

    def __init__(self, llm_service: LLMService):
        self.llm = llm_service

    def generate_answer(self, question: str, chunks: List[ChunkSchema]) -> str:
        """Generates an answer based on the provided question and context chunks."""
        logger.debug('Domain: Generating answer for question: %s', question)

        context_str = '\n---\n'.join([chunk.text_chunk for chunk in chunks])
        if not context_str:
            return "I'm sorry, I couldn't find any relevant information in the provided documents to answer your question."

        prompt = RAG_PROMPT_TEMPLATE.substitute(
            context=context_str, question=question,
        )
        try:
            return self.llm.get_completion(prompt=prompt)
        except Exception:
            logger.exception(
                'Domain: Answer generation failed', extra={'question': question},
            )
            raise
