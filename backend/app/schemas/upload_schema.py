from pydantic import BaseModel
from typing import Optional


class UploadResponseSchema(BaseModel):
    status: bool
    message: str
    data: Optional[dict] = None