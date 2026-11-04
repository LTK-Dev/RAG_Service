from pydantic import BaseModel, ConfigDict
from typing import List


class ChunkSchema(BaseModel):
    """Pydantic model for a document chunk"""

    model_config = ConfigDict(from_attributes=True)

    doc_id: int
    text_chunk: str
    embedding: List[float]
