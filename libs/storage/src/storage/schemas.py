from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from typing import Optional, Union
import io


class MinioInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    bucket_name: str
    object_name: str
    file_path: Optional[str] = None
    data: Union[bytes, io.BytesIO, None] = None
    content_type: Optional[str] = None


class MinioOutput(BaseModel):
    pass
