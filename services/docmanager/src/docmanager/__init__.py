import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from logger import setup_logging

setup_logging()

from docmanager.api.routers import document_router
from docmanager.shared.settings import get_settings
from postgres import SQLDatabase
from storage import MinioService
from llm import EmbeddingService
from open_search import OpenSearchService

logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('Server startup: Initializing resources...')
    app.state.settings = settings
    try:
        db_client = SQLDatabase(dsn=app.state.settings.postgres.dsn)
        app.state.sql_database = db_client
        logger.info('SQLDatabase client initialized.')

        minio_client = MinioService(settings=app.state.settings.minio)
        app.state.minio_service = minio_client
        logger.info('MinioService client initialized.')

        opensearch_client = OpenSearchService(settings=app.state.settings.opensearch)
        app.state.opensearch_service = opensearch_client
        logger.info('OpenSearchService client initialized.')

        embedding_client = EmbeddingService(settings=app.state.settings.embedding)
        app.state.embedding_service = embedding_client
        logger.info('EmbeddingService (model) initialized.')

    except Exception as e:
        logger.critical(
            f"CRITICAL: Failed to initialize resources during lifespan: {e}",
            exc_info=True,
        )
        raise e

    yield

    logger.info('Server shutdown: Closing resources...')
    if hasattr(app.state, 'sql_database'):
        app.state.sql_database.close_engine()
    if hasattr(app.state, 'opensearch_service'):
        app.state.opensearch_service.close_client()


app = FastAPI(title='Document Manager Service', lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # Allows all origins
    allow_credentials=True,
    allow_methods=['*'],  # Allows all methods
    allow_headers=['*'],  # Allows all headers
)


app.include_router(document_router.router, prefix='/api/v1', tags=['Documents'])


@app.get('/health', tags=['Health'])
def health_check():
    logger.info('Health check')
    return {'status': 'ok'}


def main():
    """Entry point cho console script `docmanager`."""
    uvicorn.run(
        'docmanager:app',
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.reload,
    )


__all__ = ['app', 'main']
