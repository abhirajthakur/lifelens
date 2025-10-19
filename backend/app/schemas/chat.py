from typing import List, Optional

from pydantic import BaseModel


class SendMessageRequest(BaseModel):
    message: str


class ConversationResponse(BaseModel):
    id: str
    title: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: str


class ChatResponse(BaseModel):
    conversation_id: str
    message_id: int
    response: str
    function_calls: Optional[List[dict]] = None
