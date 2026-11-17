
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, get_db
from app.models.user import User
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationResponse,
    MessageResponse,
)
from app.services.chat import (
    create_conversation,
    get_conversation,
    get_conversation_history,
    list_conversations,
    save_message,
)
from app.agent.chat_runtime import generate_chat_response


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        if request.conversation_id:
            conversation = await get_conversation(
                db=db,
                conversation_id=request.conversation_id,
                organization_id=current_user.organization_id,
                user_id=current_user.id,
            )

            if conversation is None:
                raise HTTPException(
                    status_code=404,
                    detail="Conversation not found.",
                )
        else:
            conversation = await create_conversation(
                db=db,
                organization_id=current_user.organization_id,
                user_id=current_user.id,
                title=request.message[:60],
            )

        # Retrieve previous messages before saving the new message.
        history = await get_conversation_history(
            db=db,
            conversation_id=conversation.id,
            limit=20,
        )

        user_message = await save_message(
            db=db,
            conversation_id=conversation.id,
            role="user",
            content=request.message,
        )

        history_payload = [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in history
        ]

        # Run the AI agent.
        result = await generate_chat_response(
            user_message=request.message,
            history=history_payload,
        )

        assistant_message = await save_message(
            db=db,
            conversation_id=conversation.id,
            role="assistant",
            content=result["answer"],
            sources=result.get("sources", []),
        )

        # Update conversation timestamp.
        await db.refresh(conversation)

        await db.commit()

        return ChatResponse(
            conversation_id=conversation.id,
            message_id=assistant_message.id,
            answer=result["answer"],
            sources=result.get("sources", []),
            created_at=assistant_message.created_at,
        )

    except HTTPException:
        await db.rollback()
        raise

    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Chat request failed. Please try again.",
        )


@router.get(
    "/conversations",
    response_model=list[ConversationResponse],
)
async def get_user_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversations = await list_conversations(
        db=db,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
    )

    return conversations


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[MessageResponse],
)
async def get_messages(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = await get_conversation(
        db=db,
        conversation_id=conversation_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    messages = await get_conversation_history(
        db=db,
        conversation_id=conversation.id,
        limit=100,
    )

    return messages
