import logging
from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from rag_service.application.rag.service import RAGAppService
from rag_service.api.schemas import RAGRequest, RAGResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post('/chat', response_model=RAGResponse)
async def rag_route(request: Request, rag_request: RAGRequest):
    """
    Handles the RAG QnA requests.
    """
    try:
        application = RAGAppService(request=request)

        output = await run_in_threadpool(
            application.process,
            question=rag_request.question,
            filter_doc_ids=rag_request.filter_doc_ids,
        )
        return output
    except Exception:
        logger.exception(
            'API: Caught unexpected error during QnA',
            extra={'path': request.url.path},
        )
        raise HTTPException(
            status_code=500, detail='An internal server error occurred.',
        )
