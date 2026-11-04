from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List
from postgres.schemas import DocumentStatus, DocumentSchema


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    file_name: str
    status: DocumentStatus
    created_at: datetime
