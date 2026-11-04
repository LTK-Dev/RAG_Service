import logging
from opensearchpy import OpenSearch
from .settings import OpenSearchSettings
from .controller import OpenSearchController
from .schemas import ChunkSchema
from typing import List

logger = logging.getLogger(__name__)


class OpenSearchService(OpenSearchController):

    def __init__(self, settings: OpenSearchSettings):
        self.settings = settings
        try:
            logger.info(f"Initializing OpenSearch client for host: {settings.host}")

            # Tạo auth tuple
            http_auth = (settings.http_auth_user, settings.http_auth_pass)

            self.client = OpenSearch(
                hosts=[{'host': settings.host, 'port': settings.port}],
                http_auth=http_auth,
                use_ssl=settings.use_ssl,
                verify_certs=settings.verify_certs,
                ssl_assert_hostname=settings.ssl_assert_hostname,
            )
            if not self.client.ping():
                raise ConnectionError('OpenSearch ping failed.')
            logger.info('OpenSearch client is ready.')

            # Khởi tạo Repository/Controller
            self.index_name = settings.index_name
            super().__init__(
                client=self.client,
                index_name=self.index_name,
                pipeline_name=settings.pipeline_name,
                embedding_dim=settings.embedding_dim,
            )

        except Exception as e:
            logger.critical(
                f"CRITICAL: Failed to initialize OpenSearch client: {e}", exc_info=True,
            )
            raise

    def close_client(self):
        """Closes the OpenSearch client connection."""
        if self.client:
            logger.info('Closing OpenSearch client connection...')
            self.client.close()
