
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="The user's message",
    )
    conversation_id: UUID | None = None


class ChatSource(BaseModel):
    title: str
    url: str
    snippet: str


class ChatResponse(BaseModel):
    conversation_id: UUID
    message_id: UUID
    answer: str
    sources: list[ChatSource] = Field(default_factory=list)
    created_at: datetime


class ConversationResponse(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    sources: list[ChatSource] = Field(default_factory=list)
    created_at: datetime
