from __future__ import annotations

import logging
from typing import List
from typing import Optional

from docmanager.api.schemas import DocumentResponse
from docmanager.application.createDocument import CreateDocumentAppService
from docmanager.application.deleteDocument import DeleteDocumentAppService
from docmanager.application.getDocument import GetDocumentsAppService
from fastapi import APIRouter
from fastapi import BackgroundTasks
from fastapi import File
from fastapi import HTTPException
from fastapi import Query
from fastapi import Request
from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool
from postgres.schemas import DocumentStatus
from starlette.status import HTTP_204_NO_CONTENT


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get('/documents', response_model=List[DocumentResponse])
async def get_documents(
    request: Request,
    status: Optional[DocumentStatus] = Query(
        None, description='Filter by document status',
    ),
    order_by: Optional[str] = Query(
        'created_at:desc',
        description="Sort by field (e.g., 'created_at:desc')",
    ),
    limit: int = Query(20, ge=1, le=1000, description='Page size limit'),
):
    """Handles the request to retrieve documents."""
    try:
        application = GetDocumentsAppService(request=request)
        output = await run_in_threadpool(
            application.process, status=status, order_by=order_by, limit=limit,
        )
        return output

    except Exception:
        logger.exception(
            'API: Unexpected error', extra={
                'path': request.url.path,
            },
        )
        raise HTTPException(status_code=500, detail='Internal server error.')


@router.post('/documents', response_model=DocumentResponse, status_code=201)
async def create_document_route(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """
    Handles the request to upload one document.
    """
    try:
        application = CreateDocumentAppService(request=request)
        output = await run_in_threadpool(
            application.process, upload_file=file,
            background_tasks=background_tasks,
        )
        return output

    except Exception:
        logger.exception(
            'API: Unexpected error', extra={
                'path': request.url.path,
            },
        )
        raise HTTPException(
            status_code=500, detail='An internal server error occurred.',
        )


@router.delete('/documents/{doc_id}', status_code=HTTP_204_NO_CONTENT)
async def delete_document_route(
    request: Request,
    doc_id: int,
) -> None:
    """
    Handles the request to delete a document.
    """
    try:
        application = DeleteDocumentAppService(request=request)
        await run_in_threadpool(application.process, doc_id=doc_id)
    except Exception:
        logger.exception(
            'API: Caught unexpected error during deletion',
            extra={'doc_id': doc_id},
        )
        raise HTTPException(
            status_code=500, detail='An internal server error occurred.',
        )
