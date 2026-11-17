
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_message import ChatMessage
from app.models.conversation import Conversation


async def create_conversation(
    db: AsyncSession,
    organization_id: UUID,
    user_id: UUID,
    title: str = "New conversation",
) -> Conversation:
    conversation = Conversation(
        organization_id=organization_id,
        user_id=user_id,
        title=title[:255],
    )

    db.add(conversation)
    await db.flush()
    await db.refresh(conversation)

    return conversation


async def get_conversation(
    db: AsyncSession,
    conversation_id: UUID,
    organization_id: UUID,
    user_id: UUID,
) -> Conversation | None:
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.organization_id == organization_id,
            Conversation.user_id == user_id,
        )
    )

    return result.scalar_one_or_none()


async def save_message(
    db: AsyncSession,
    conversation_id: UUID,
    role: str,
    content: str,
    sources: list | None = None,
) -> ChatMessage:
    if role not in {"user", "assistant"}:
        raise ValueError("Invalid chat message role.")

    message = ChatMessage(
        conversation_id=conversation_id,
        role=role,
        content=content,
        sources=sources or [],
    )

    db.add(message)
    await db.flush()

    # Update the parent conversation's activity timestamp.
    await db.execute(
        update(Conversation)
        .where(Conversation.id == conversation_id)
        .values(updated_at=func.now())
    )
    await db.flush()
    await db.refresh(message)

    return message


async def get_conversation_history(
    db: AsyncSession,
    conversation_id: UUID,
    limit: int = 20,
) -> list[ChatMessage]:
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
        .limit(limit)
    )

    messages = list(result.scalars().all())
    messages.reverse()

    return messages


async def list_conversations(
    db: AsyncSession,
    organization_id: UUID,
    user_id: UUID,
    limit: int = 50,
) -> list[Conversation]:
    result = await db.execute(
        select(Conversation)
        .where(
            Conversation.organization_id == organization_id,
            Conversation.user_id == user_id,
        )
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
    )

    return list(result.scalars().all())