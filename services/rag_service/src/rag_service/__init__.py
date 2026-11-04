import logging
from fastapi import FastAPI
import uvicorn
from contextlib import asynccontextmanager
from logger import setup_logging
from fastapi.middleware.cors import CORSMiddleware


setup_logging()

from rag_service.api.routers import rag_router
from open_search import OpenSearchService
from llm import LLMService, EmbeddingService
from rag_service.shared.settings import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('RAG Service startup: Initializing resources...')
    app.state.settings = settings

    try:
        # Tiêm API Key vào LiteLLM
        app.state.llm_service = LLMService(settings=app.state.settings.llm)
        # Khởi tạo các client
        app.state.opensearch_service = OpenSearchService(
            settings=app.state.settings.opensearch,
        )
        app.state.embedding_service = EmbeddingService(settings=app.state.settings.embedding)
        logger.info('RAG Service resources initialized.')
    except Exception as e:
        logger.critical(
            f"CRITICAL: Failed to initialize RAG resources: {e}", exc_info=True,
        )
        raise e

    yield

    logger.info('RAG Service shutdown: Closing resources...')
    if hasattr(app.state, 'opensearch_service'):
        app.state.opensearch_service.close_client()


app = FastAPI(title='RAG Service', lifespan=lifespan)

app.include_router(rag_router.router, prefix='/api/v1', tags=['RAG'])


app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # Allows all origins
    allow_credentials=True,
    allow_methods=['*'],  # Allows all methods
    allow_headers=['*'],  # Allows all headers
)

@app.get('/health', tags=['Health'])
def health_check():
    logger.info('Health check')
    return {'status': 'ok'}


def main():
    uvicorn.run(
        'rag_service:app',
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.reload,
    )


__all__ = ['app', 'main']
