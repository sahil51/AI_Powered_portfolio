import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from infrastructure.cache.redis_client import CacheService, get_redis
from infrastructure.llm.litellm_client import LiteLLMClient
from memory.long_term.service import LongTermMemory
from memory.short_term.service import ShortTermMemory
from middleware.audit import log_audit
from middleware.auth import get_optional_user
from monitoring.logger import logger
from rag.embeddings.service import EmbeddingService
from rag.retrieval.service import RetrievalService
from services.conversation_service import ConversationService

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[str] = None
    user_type: str = Field(default="visitor", pattern="^(visitor|recruiter|client)$")
    idempotency_key: Optional[str] = None


class ChatResponse(BaseModel):
    conversation_id: str
    message: str
    needs_confirmation: bool = False
    workflow_state: str = "idle"
    intent: Optional[str] = None


async def get_chat_service(request: Request) -> tuple[ConversationService, CacheService]:
    llm = LiteLLMClient()
    redis = await get_redis()
    cache_service = CacheService(redis)
    short_term_memory = ShortTermMemory(cache_service)
    embedding_service = EmbeddingService()
    retrieval_service = RetrievalService(embedding_service)

    session = request.app.state.db_session

    async def get_long_term_memory():
        async with session() as db_session:
            return LongTermMemory(db_session)

    service = ConversationService(
        llm=llm,
        short_term_memory=short_term_memory,
        long_term_memory=await get_long_term_memory(),
        retrieval_service=retrieval_service,
    )
    return service, cache_service


@router.post("/message", response_model=ChatResponse)
async def chat_message(
    chat_request: ChatRequest,
    request: Request,
    user: Optional[dict] = Depends(get_optional_user),
):
    user_id = getattr(request.state, "user_id", "anonymous")
    identity_source = getattr(request.state, "identity_source", "anonymous")
    email = getattr(request.state, "email", None)
    session_id = getattr(request.state, "session_id", None)

    if user and identity_source == "anonymous":
        user_id = user.get("sub", "anonymous")
        identity_source = "jwt"
        email = user.get("email", email)
        request.state.user_id = user_id
        request.state.identity_source = identity_source
        request.state.email = email

    service, cache = await get_chat_service(request)
    conversation_id = chat_request.conversation_id or str(uuid.uuid4())

    idempotency_key = chat_request.idempotency_key
    if idempotency_key:
        cached = await cache.check_idempotency(idempotency_key)
        if cached:
            logger.info(f"Idempotency hit for key={idempotency_key}", extra={"conversation_id": conversation_id})
            return ChatResponse(**cached)

    lock_acquired = await cache.acquire_conversation_lock(conversation_id)
    if not lock_acquired:
        logger.warning(f"Conversation lock contention: {conversation_id}")
        raise HTTPException(
            status_code=409,
            detail="Conversation is currently being processed. Please try again.",
            headers={"Retry-After": "1"},
        )

    logger.info(
        "Chat message received",
        extra={
            "user_id": user_id,
            "session_id": session_id or user_id,
            "identity_source": identity_source,
            "user_type": chat_request.user_type,
            "conversation_id": conversation_id,
            "message_length": len(chat_request.message),
        },
    )

    try:
        result = await service.process_message(
            user_id=user_id,
            message=chat_request.message,
            user_type=chat_request.user_type,
            conversation_id=conversation_id,
        )

        response = ChatResponse(
            conversation_id=result["conversation_id"],
            message=result["response"],
            needs_confirmation=result.get("needs_confirmation", False),
            workflow_state=result.get("workflow_state", "idle"),
            intent=result.get("intent"),
        )

        if idempotency_key:
            await cache.set_idempotency(
                idempotency_key, response.model_dump()
            )

        await log_audit(
            action="chat_message",
            entity_type="conversation",
            entity_id=result["conversation_id"],
            user_id=user_id,
            conversation_id=result["conversation_id"],
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process message")
    finally:
        await cache.release_conversation_lock(conversation_id)


@router.post("/message/sync")
async def chat_message_sync(
    chat_request: ChatRequest,
    request: Request,
):
    return await chat_message(chat_request, request, None)
