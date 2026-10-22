import asyncio
import json
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import ApiError
from app.core.limits import consume, lock_ai_capacity
from app.db.models import AIConversation, AIMessage, AIUsage, Exercise, User
from app.modules.ai import context, prompts
from app.modules.ai.provider import Completion, Provider
from app.modules.ai.schemas import (
    ChatRequest,
    ExplainRequest,
    Explanation,
    GeneratedExercise,
    GenerateRequest,
)
from app.modules.gamification.service import lock_learner

# Global process bound; persistent per-user leases below also coordinate workers.
_active = 0


@asynccontextmanager
async def capacity(settings: Settings):
    global _active
    if _active >= settings.ai_concurrency:
        raise ApiError(429, "AI_BUSY", "AI is busy; try again shortly")
    _active += 1
    try:
        yield
    finally:
        _active -= 1


def validate_input(value: str, settings: Settings) -> None:
    if not value.strip() or len(value) > settings.ai_max_input_chars:
        raise ApiError(422, "AI_INPUT_LIMIT", "AI input is empty or too long")


async def owned_conversation(
    db: AsyncSession, user_id: UUID, conversation_id: UUID
) -> AIConversation:
    conversation = await db.scalar(
        select(AIConversation).where(
            AIConversation.id == conversation_id, AIConversation.user_id == user_id
        )
    )
    if conversation is None:
        raise ApiError(404, "NOT_FOUND", "Conversation not found")
    return conversation


async def prepare_chat(db: AsyncSession, user: User, payload: ChatRequest, settings: Settings):
    validate_input(payload.message, settings)
    await lock_learner(db, user.id)
    history = []
    conversation = None
    if payload.conversation_id:
        conversation = await owned_conversation(db, user.id, payload.conversation_id)
        count = (
            await db.scalar(
                select(func.count())
                .select_from(AIMessage)
                .where(AIMessage.conversation_id == conversation.id)
            )
            or 0
        )
        if count + 2 > settings.ai_messages_per_conversation:
            raise ApiError(409, "AI_HISTORY_LIMIT", "Start a new conversation")
        recent = list(
            (
                await db.scalars(
                    select(AIMessage)
                    .where(AIMessage.conversation_id == conversation.id)
                    .order_by(AIMessage.created_at.desc(), AIMessage.id.desc())
                    .limit(settings.ai_history_messages)
                )
            ).all()
        )
        chars = 0
        for message in recent:
            if chars + len(message.content) > settings.ai_history_chars:
                break
            chars += len(message.content)
            history.append({"role": message.role, "content": message.content})
        history.reverse()
    else:
        count = (
            await db.scalar(
                select(func.count())
                .select_from(AIConversation)
                .where(AIConversation.user_id == user.id)
            )
            or 0
        )
        if count >= settings.ai_conversations_per_user:
            raise ApiError(409, "AI_CONVERSATION_LIMIT", "Delete an old conversation first")
    learner = await context.learner_context(db, user, payload.lesson_id)
    learner["correct_grammar"] = payload.correct_grammar
    return conversation, prompts.messages(learner, payload.message, history)


async def reserve(
    db: AsyncSession, user: User, settings: Settings, messages: list[dict]
) -> AIUsage:
    await lock_learner(db, user.id)
    now = datetime.now(UTC)
    lease_start = now - timedelta(seconds=settings.ai_request_timeout + 60)
    if await db.scalar(
        select(AIUsage.id)
        .where(
            AIUsage.user_id == user.id,
            AIUsage.status == "reserved",
            AIUsage.created_at > lease_start,
        )
        .limit(1)
    ):
        raise ApiError(429, "AI_BUSY", "An AI request is already running")
    await lock_ai_capacity(db)
    active = (
        await db.scalar(
            select(func.count())
            .select_from(AIUsage)
            .where(AIUsage.status == "reserved", AIUsage.created_at > lease_start)
        )
        or 0
    )
    if active >= settings.ai_concurrency:
        raise ApiError(429, "AI_BUSY", "AI is busy; try again shortly")
    await consume(db, f"ai:minute:{user.id}", settings.ai_requests_per_minute, 60)
    await consume(db, f"ai:day:{user.id}", settings.ai_daily_requests, 86400)
    # Conservative token reservation: UTF-8 bytes upper-bound text tokens.
    tokens = (
        sum(len(m["content"].encode()) for m in messages)
        + 32 * len(messages)
        + settings.ai_max_output_tokens
    )
    spent = (
        await db.scalar(
            select(func.sum(AIUsage.reserved_tokens)).where(
                AIUsage.user_id == user.id,
                AIUsage.created_at >= now.replace(hour=0, minute=0, second=0, microsecond=0),
            )
        )
        or 0
    )
    if spent + tokens > settings.ai_daily_token_budget:
        raise ApiError(429, "AI_BUDGET_LIMIT", "Daily AI budget reached")
    await db.execute(
        delete(AIUsage)
        .where(AIUsage.created_at < now - timedelta(days=30))
        .execution_options(synchronize_session="fetch")
    )
    usage = AIUsage(
        user_id=user.id, model=settings.openrouter_model, status="reserved", reserved_tokens=tokens
    )
    db.add(usage)
    await db.commit()
    return usage


async def finish_usage(db: AsyncSession, usage: AIUsage, result: Completion | None) -> None:
    usage.status = "completed" if result else "failed"
    usage.usage = result.usage if result else None
    # Failed/unknown requests retain reservation: cancellation can still incur costs.
    await db.commit()


async def save_turn(
    db: AsyncSession,
    user: User,
    conversation: AIConversation | None,
    payload: ChatRequest,
    result: Completion,
    usage: AIUsage,
) -> tuple[AIConversation, AIMessage]:
    await lock_learner(db, user.id)
    if conversation:
        conversation = await owned_conversation(db, user.id, conversation.id)
    else:
        conversation = AIConversation(user_id=user.id, model=result.model)
        db.add(conversation)
        await db.flush()
    # Ordered timestamps keep paired turns deterministic even on low-resolution databases.
    now = datetime.now(UTC)
    db.add(
        AIMessage(
            conversation_id=conversation.id,
            role="user",
            content=payload.message,
            model=result.model,
            created_at=now,
        )
    )
    answer = AIMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=result.content,
        model=result.model,
        usage=result.usage,
        created_at=now + timedelta(microseconds=1),
    )
    db.add(answer)
    usage.status, usage.usage = "completed", result.usage
    await db.commit()
    await db.refresh(answer)
    return conversation, answer


async def chat(
    db: AsyncSession, user: User, payload: ChatRequest, settings: Settings, provider: Provider
):
    async with capacity(settings):
        conversation, messages = await prepare_chat(db, user, payload, settings)
        usage = await reserve(db, user, settings, messages)
        try:
            async with asyncio.timeout(settings.ai_request_timeout):
                result = await provider.complete(messages)
            return await save_turn(db, user, conversation, payload, result, usage)
        except BaseException:
            await db.rollback()
            await finish_usage(db, usage, None)
            raise


async def structured(
    db: AsyncSession,
    user: User,
    payload: ExplainRequest | GenerateRequest,
    settings: Settings,
    provider: Provider,
):
    async with capacity(settings):
        lesson_id = payload.lesson_id if isinstance(payload, ExplainRequest) else None
        extra = {}
        schema_type: type[Explanation] | type[GeneratedExercise]
        if isinstance(payload, ExplainRequest):
            validate_input(payload.student_answer, settings)
            if payload.exercise_id:
                exercise = await db.get(Exercise, payload.exercise_id)
                if exercise is None or (lesson_id and lesson_id != exercise.lesson_id):
                    raise ApiError(404, "NOT_FOUND", "Exercise not found")
                lesson_id = exercise.lesson_id
                extra["exercise_prompt"] = exercise.prompt[:2000]
                # Official answer keys are deliberately excluded.
            schema_type, task = Explanation, "explain"
        else:
            schema_type, task = GeneratedExercise, "generate"
        learner = await context.learner_context(db, user, lesson_id)
        if isinstance(payload, GenerateRequest) and payload.level:
            learner["level"] = payload.level
        learner.update(extra)
        schema = schema_type.model_json_schema(by_alias=False)
        request = json.dumps(payload.model_dump(mode="json", exclude_none=True))
        validate_input(request, settings)
        messages = prompts.messages(learner, request, task=task, schema=schema)
        usage = await reserve(db, user, settings, messages)
        try:
            async with asyncio.timeout(settings.ai_request_timeout):
                result = await provider.complete(messages, schema)
            parsed = schema_type.model_validate_json(result.content)
            if isinstance(payload, GenerateRequest) and (
                not isinstance(parsed, GeneratedExercise) or parsed.type != payload.exercise_type
            ):
                raise ValueError("Exercise type mismatch")
            await finish_usage(db, usage, result)
            return parsed
        except (ValidationError, ValueError) as exc:
            await finish_usage(db, usage, None)
            raise ApiError(
                502, "AI_INVALID_RESPONSE", "AI returned invalid practice material"
            ) from exc
        except BaseException:
            await db.rollback()
            await finish_usage(db, usage, None)
            raise
