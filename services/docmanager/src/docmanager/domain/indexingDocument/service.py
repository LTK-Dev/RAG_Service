import logging
from typing import List
from postgres import SQLDatabase
from open_search import OpenSearchService
from llm import EmbeddingService
from open_search.schemas import ChunkSchema
from docmanager.shared.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class IndexingDomainService:
    def __init__(
        self,
        sql_database: SQLDatabase,
        opensearch_service: OpenSearchService,
        embedding_service: EmbeddingService,
    ):
        self.db = sql_database
        self.search = opensearch_service
        self.embed = embedding_service

    def index_document_chunks(self, doc_id: int, text_chunks: List[str]):
        """
        Domain logic to embed text chunks and index them in OpenSearch.
        """
        logger.debug(f"Domain: Processing document ID {doc_id}...")

        try:
            # Embedding
            vectors = self.embed.get_embeddings(text_chunks)

            # Chuẩn bị (Format) để Index
            chunks_to_index: List[ChunkSchema] = []
            for i, chunk_text in enumerate(text_chunks):
                chunk_schema = ChunkSchema(
                    doc_id=doc_id, text_chunk=chunk_text, embedding=vectors[i],
                )
                chunks_to_index.append(chunk_schema)

            # Index (Lưu vào OpenSearch)
            self.search.index_chunks(chunks=chunks_to_index)

            logger.info(
                f"Domain: Successfully processed and indexed document ID {doc_id}.",
            )

        except Exception as e:
            logger.exception(
                f"Domain: Failed to process document ID {doc_id}",
                extra={'doc_id': doc_id},
            )
            raise DatabaseError(f"Error in domain layer: {e}")
