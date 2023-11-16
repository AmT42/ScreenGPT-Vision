from pydantic import BaseModel
from typing import List, Optional

class ChatInput(BaseModel):
    text: Optional[str] = None
    images: Optional[List[str]] = None