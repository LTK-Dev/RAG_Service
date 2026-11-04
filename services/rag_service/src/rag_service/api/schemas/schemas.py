from pydantic import BaseModel
from typing import List, Optional, Any


class RAGRequest(BaseModel):
    question: str
    filter_doc_ids: Optional[List[int]] = None


class ContextChunkResponse(BaseModel):
    doc_id: int
    text_chunk: str


class RAGResponse(BaseModel):
    answer: str
    context: List[ContextChunkResponse]
