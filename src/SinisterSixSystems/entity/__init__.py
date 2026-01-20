from pydantic import BaseModel
from typing import Dict, Any

class ChatRequest(BaseModel):
    query: str
    document: str | None = None