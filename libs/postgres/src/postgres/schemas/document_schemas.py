from pydantic import BaseModel, ConfigDict
from datetime import datetime
from enum import Enum


class DocumentStatus(str, Enum):
    PENDING = 'PENDING'
    PROCESSING = 'PROCESSING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'


# Schema for API
class DocumentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    file_name: str
    minio_path: str
    status: DocumentStatus
    created_at: datetime
