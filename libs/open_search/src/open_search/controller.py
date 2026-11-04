import logging
from typing import List, cast, Dict
from opensearchpy import OpenSearch, helpers
from typing import List, Optional, Any, Sequence
from .schemas import ChunkSchema
from .repository import IOpenSearchRepository

logger = logging.getLogger(__name__)


class OpenSearchController(IOpenSearchRepository):
    def __init__(
        self,
        client: OpenSearch,
        index_name: str,
        pipeline_name: str,
        embedding_dim: int,
    ):
        self.client = client
        self.index_name = index_name
        self.pipeline_name = pipeline_name
        self.embedding_dim = embedding_dim
        self._initialize_opensearch()

    def _initialize_opensearch(self):
        """
        Initializes OpenSearch resources.

        1. Ensures the search pipeline (Min-Max) exists.
        2. Ensures the index exists and has the correct KNN mapping.
        """

        # --- TẠO SEARCH PIPELINE  ---
        try:

            self.client.search_pipeline.get(id=self.pipeline_name)
            logger.info(f"Search pipeline '{self.pipeline_name}' exists.")
        except Exception:
            logger.warning(
                f"Search pipeline '{self.pipeline_name}' not found. Creating...",
            )
            pipeline_body = {
                'description': 'Post processor for Min-Max hybrid search',
                'phase_results_processors': [
                    {
                        'normalization-processor': {
                            'normalization': {'technique': 'min_max'},
                            'combination': {
                                'technique': 'arithmetic_mean',
                                'parameters': {
                                    'weights': [0.3, 0.7],  # (Text 0.3, Vector 0.7)
                                },
                            },
                        },
                    },
                ],
            }
            try:
                self.client.search_pipeline.put(
                    id=self.pipeline_name, body=pipeline_body,
                )
                logger.info(
                    f"Successfully created search pipeline: {self.pipeline_name}",
                )
            except Exception as e:
                logger.critical(
                    f"CRITICAL: Failed to create search pipeline: {e}", exc_info=True,
                )
                raise e

        # ---TẠO INDEX---
        if not self.client.indices.exists(index=self.index_name):
            index_body = {
                'settings': {'index': {'knn': True, 'knn.algo_param.ef_search': 100}},
                'mappings': {
                    'properties': {
                        'embedding': {
                            'type': 'knn_vector',
                            'dimension': self.embedding_dim,
                            'method': {
                                'name': 'hnsw',
                                'space_type': 'l2',
                                'engine': 'nmslib',
                            },
                        },
                        'doc_id': {'type': 'integer'},
                        'text_chunk': {'type': 'text'},
                    },
                },
            }
            logger.warning(
                f"Index '{self.index_name}' not found. Creating with {self.embedding_dim}-dim KNN mapping...",
            )
            self.client.indices.create(index=self.index_name, body=index_body)
        else:
            logger.info(f"Index '{self.index_name}' exists.")

    def index_chunks(self, chunks: List[ChunkSchema]) -> bool:
        """Indexes a batch of document chunks into OpenSearch."""
        logger.debug(f"Indexing {len(chunks)} chunks...")

        actions = [
            {
                '_index': self.index_name,
                '_id': f"{chunk.doc_id}_{i}",  # Tạo ID duy nhất
                '_source': chunk.model_dump(),
            }
            for i, chunk in enumerate(chunks)
        ]

        try:
            success, failed = helpers.bulk(self.client, actions, raise_on_error=False)
            if failed:
                logger.error(f"Failed to index {len(failed)} chunks: {failed}")
                return False
            logger.info(f"Successfully indexed {success} chunks.")
            return True
        except Exception as e:
            logger.exception('Error during OpenSearch bulk indexing')
            raise e

    def delete_chunks_by_doc_id(self, doc_id: int) -> dict:
        """
        Deletes all documents/chunks in OpenSearch that match a doc_id.
        """
        logger.debug(f"Repository: Deleting chunks for doc_id {doc_id}...")

        query = {'query': {'term': {'doc_id': doc_id}}}

        try:
            response = self.client.delete_by_query(
                index=self.index_name,
                body=query,
                wait_for_completion=True,  # Chờ cho đến khi xóa xong
            )
            logger.info(
                f"Repository: Delete_by_query response for doc_id {doc_id}: {response}",
            )
            return response
        except Exception as e:
            logger.exception(
                'Repository: OpenSearch error deleting by doc_id',
                extra={'doc_id': doc_id},
            )
            raise e

    def hybrid_search_min_max(
        self,
        question_text: str,
        question_vector: List[float],
        k: int,
        filter_doc_ids: Optional[List[int]] = None,
    ) -> List[ChunkSchema]:
        """Performs a hybrid search (text + vector) using a min-max normalization pipeline.

        Args:
            question_text (str): The user's question.
            question_vector (List[float]): The embedding vector of the question.
            k (int): The number of top results to return.
            filter_doc_ids (Optional[List[int]]): A list of document IDs to filter the search by.

        Returns:
            List[ChunkSchema]: A list of relevant document chunks.
        """
        logger.debug(f"Repository: Running Min-Max Hybrid Search (using KNN)...")

        # Truy vấn con cho Text Search (Weight 0.3)
        text_query = {'match': {'text_chunk': question_text}}

        # Truy vấn con cho Vector Search (Weight 0.7)
        vector_query = {
            'knn': {
                'embedding': {
                    'vector': question_vector,
                    'k': 50,  # (Lấy nhiều hơn 5 để Pipeline xếp hạng)
                },
            },
        }

        # Xây dựng truy vấn chính
        query_body: Dict[str, Any] = {
            'size': k,
            'query': {
                'hybrid': {
                    'queries': [
                        text_query,  # <-- Query 0 (weight 0.3)
                        vector_query,  # <-- Query 1 (weight 0.7)
                    ],
                },
            },
        }

        # Áp dụng Filter
        if filter_doc_ids:
            query_body['query'] = {
                'bool': {
                    'must': {'hybrid': query_body['query']['hybrid']},
                    'filter': [{'terms': {'doc_id': filter_doc_ids}}],
                },
            }

        try:

            response = self.client.search(
                index=self.index_name,
                body=query_body,
                search_pipeline=self.pipeline_name,
            )

            # Map kết quả
            chunks = []
            for hit in response['hits']['hits']:
                chunks.append(ChunkSchema.model_validate(hit['_source']))
            return chunks

        except Exception as e:
            logger.exception(
                'Repository: OpenSearch Min-Max Search failed',
                extra={'query': query_body},
            )
            raise e
