from pydantic import BaseModel
from typing import List, Optional


class TextRequest(BaseModel):
    text: str


class ResponseItem(BaseModel):
    id: int
    requirement: str
    is_met: Optional[bool] = None
    file_name: Optional[str] = None
    citation: Optional[str] = None
    explanation: Optional[str] = None
    top_k: Optional[int] = 3


class PolicyRow(BaseModel):
    file_name: str
    section: str
    paragraph_id: Optional[int] = None
    content: str
    embedding: Optional[List[float]] = None
