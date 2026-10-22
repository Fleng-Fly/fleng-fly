import asyncio
import json
from contextlib import aclosing
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import Settings, get_settings
from app.core.errors import ApiError
from app.db.models import AIConversation, AIMessage, User
from app.db.session import get_db
from app.modules.ai import context, service
from app.modules.ai.provider import Completion, Provider, get_provider
from app.modules.ai.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationResponse,
    ExplainRequest,
    Explanation,
    GeneratedExercise,
    GenerateRequest,
    MessageResponse,
)
from app.modules.gamification.service import lock_learner

router = APIRouter(prefix="/ai", tags=["ai"])


def provider_dependency(settings: Settings = Depends(get_settings)) -> Provider:
    return get_provider(settings)


def chat_response(conversation, message):
    return ChatResponse(
        conversation_id=conversation.id,
        message=MessageResponse.model_validate(message, from_attributes=True),
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    provider: Provider = Depends(provider_dependency),
):
    try:
        conversation, answer = await service.chat(db, user, payload, settings, provider)
        return chat_response(conversation, answer)
    except TimeoutError as exc:
        raise ApiError(504, "AI_TIMEOUT", "AI request timed out") from exc


@router.get("/conversations", response_model=list[ConversationResponse])
async def conversations(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return (
        await db.scalars(
            select(AIConversation)
            .where(AIConversation.user_id == user.id)
            .order_by(AIConversation.created_at.desc(), AIConversation.id)
            .limit(limit)
            .offset(offset)
        )
    ).all()


@router.get("/conversations/{conversation_id}", response_model=list[MessageResponse])
async def history(
    conversation_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await service.owned_conversation(db, user.id, conversation_id)
    return (
        await db.scalars(
            select(AIMessage)
            .where(AIMessage.conversation_id == conversation_id)
            .order_by(AIMessage.created_at, AIMessage.id)
            .limit(limit)
            .offset(offset)
        )
    ).all()


@router.delete("/conversations/{conversation_id}", status_code=204)
async def remove(
    conversation_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await lock_learner(db, user.id)
    conversation = await service.owned_conversation(db, user.id, conversation_id)
    await db.execute(delete(AIMessage).where(AIMessage.conversation_id == conversation.id))
    await db.delete(conversation)
    await db.commit()


@router.post("/explain", response_model=Explanation)
async def explain(
    payload: ExplainRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    provider: Provider = Depends(provider_dependency),
):
    try:
        return await service.structured(db, user, payload, settings, provider)
    except TimeoutError as exc:
        raise ApiError(504, "AI_TIMEOUT", "AI request timed out") from exc


@router.post("/generate-exercise", response_model=GeneratedExercise)
async def generate(
    payload: GenerateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    provider: Provider = Depends(provider_dependency),
):
    try:
        return await service.structured(db, user, payload, settings, provider)
    except TimeoutError as exc:
        raise ApiError(504, "AI_TIMEOUT", "AI request timed out") from exc


@router.get("/recommendations")
async def recommendations(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await context.recommendations(db, user)


def event(name: str, data: dict) -> str:
    return "event: " + name + "\ndata: " + json.dumps(data) + "\n\n"


@router.post("/chat/stream")
async def stream_chat(
    payload: ChatRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    provider: Provider = Depends(provider_dependency),
):
    conversation, messages = await service.prepare_chat(db, user, payload, settings)
    usage = await service.reserve(db, user, settings, messages)

    async def stream():
        completed = False
        try:
            async with service.capacity(settings):
                content, usage_info = "", {}
                async with asyncio.timeout(settings.ai_request_timeout):
                    async with aclosing(provider.stream(messages)) as chunks:
                        async for chunk in chunks:
                            if await request.is_disconnected():
                                return
                            content += chunk.content
                            usage_info.update(chunk.usage)
                            if chunk.content:
                                yield event("delta", {"content": chunk.content})
                if await request.is_disconnected():
                    return
                result = Completion(content, settings.openrouter_model, usage_info)
                saved_conversation, answer = await service.save_turn(
                    db, user, conversation, payload, result, usage
                )
                completed = True
                yield event(
                    "done",
                    chat_response(saved_conversation, answer).model_dump(
                        mode="json", by_alias=True
                    ),
                )
        except asyncio.CancelledError:
            raise
        except (ApiError, TimeoutError) as exc:
            code = exc.code if isinstance(exc, ApiError) else "AI_TIMEOUT"
            yield event(
                "error",
                {"code": code, "message": "AI stream did not complete; retry with /ai/chat."},
            )
        except Exception:
            yield event(
                "error", {"code": "AI_UNAVAILABLE", "message": "AI stream did not complete."}
            )
        finally:
            if not completed:

                async def cleanup():
                    await db.rollback()
                    await service.finish_usage(db, usage, None)

                task = asyncio.create_task(cleanup())
                try:
                    await asyncio.shield(task)
                except asyncio.CancelledError:
                    await task

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
