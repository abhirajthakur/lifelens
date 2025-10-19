from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException
from fastapi import Query as QueryParam
from starlette.responses import StreamingResponse

from app.core.db import DBSession
from app.core.deps import CurrentUser
from app.schemas.chat import (
    ChatResponse,
    ConversationResponse,
    MessageResponse,
    SendMessageRequest,
)
from app.services.chat_services import (
    create_conversation,
    delete_conversation,
    get_conversation,
    get_conversation_messages,
    list_conversations,
    process_chat_message_stream,
)


router = APIRouter(prefix="/api/chat")


@router.post("/conversations", response_model=ConversationResponse)
async def create_new_conversation(db: DBSession, current_user: CurrentUser):
    try:
        conversation = create_conversation(db, current_user.id)

        return ConversationResponse(
            id=str(conversation.id),
            created_at=conversation.created_at.isoformat(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create conversation: {str(e)}"
        )


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    db: DBSession,
    current_user: CurrentUser,
    skip: int = QueryParam(0, ge=0),
    limit: int = QueryParam(10, ge=1, le=100),
):
    try:
        conversations = list_conversations(
            db,
            current_user.id,
            skip,
            limit,
        )

        return [
            ConversationResponse(
                id=str(conv.id),
                title=conv.title,
                created_at=conv.created_at.isoformat(),
                updated_at=conv.updated_at.isoformat(),
            )
            for conv in conversations
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve conversations: {str(e)}"
        )


@router.get(
    "/conversations/{conversation_id}/messages", response_model=List[MessageResponse]
)
async def get_messages(
    conversation_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
    limit: Optional[int] = QueryParam(None, ge=1, le=100),
):
    conversation = get_conversation(db, conversation_id, current_user.id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = get_conversation_messages(db, conversation_id, limit)

    return [
        MessageResponse(
            id=msg.id,
            role=msg.role.value,
            content=msg.content,
            created_at=msg.created_at.isoformat(),
        )
        for msg in messages
    ]


@router.post("/conversations/{conversation_id}/messages", response_model=ChatResponse)
async def send_message(
    conversation_id: UUID,
    request: SendMessageRequest,
    db: DBSession,
    current_user: CurrentUser,
):
    """
    For streaming, the response format is Server-Sent Events:
    - `{"type": "function_call", "name": "...", "args": {...}}` - Function being called
    - `{"type": "text", "content": "..."}` - Text chunk
    - `{"type": "done", "message_id": 123}` - Response complete
    - `{"type": "error", "message": "..."}` - Error occurred
    """

    return StreamingResponse(
        process_chat_message_stream(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id,
            message=request.message,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation_endpoint(
    conversation_id: UUID, db: DBSession, current_user: CurrentUser
):
    success = delete_conversation(db, conversation_id, current_user.id)

    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"message": "Conversation deleted successfully"}
