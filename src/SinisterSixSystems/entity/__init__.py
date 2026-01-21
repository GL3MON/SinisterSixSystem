from pydantic import BaseModel
from typing import Dict, Any

class ChatRequest(BaseModel):
    query: str
    document: str | None = None

class AudioRequest(BaseModel):
    mode: str
    query: str

class VideoRequest(BaseModel):
    query: str