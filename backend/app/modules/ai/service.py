import asyncio
import json
import math
from contextlib import asynccontextmanager
from datetime import UTC, datetime, time, timedelta
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import case, delete, func, select, update
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import ApiError
from app.core.limits import consume, lock_ai_capacity
from app.db.models import AIConversation, AIMessage, AIUsage, Exercise, User
from app.modules.ai import billing, context, prompts
from app.modules.ai.provider import (
    Completion,
    NotBilled,
    Provider,
    UpstreamRefused,
    priced,
    unavailable,
)
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
    if not value.strip() or len(value) > settings.ai_max_message_length:
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
    if payload.current_answer and payload.current_answer.strip():
        validate_input(payload.current_answer, settings)
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
    if payload.exercise_id and payload.lesson_id and "lesson" in learner:
        exercise = await db.scalar(
            select(Exercise).where(
                Exercise.id == payload.exercise_id, Exercise.lesson_id == payload.lesson_id
            )
        )
        if exercise is not None:
            learner["exercise"] = await context.exercise_context(
                db, user, exercise, payload.current_answer
            )
    learner["correct_grammar"] = payload.correct_grammar
    task = "exercise_help" if "exercise" in learner else "tutor"
    return conversation, prompts.messages(learner, payload.message, history, task=task)


def utcnow() -> datetime:
    """Single clock for AI quotas; daily windows are UTC calendar days."""
    return datetime.now(UTC)


def until_next_utc_day(now: datetime) -> dict[str, str]:
    tomorrow = datetime.combine(now.date() + timedelta(days=1), time(), UTC)
    return {"Retry-After": str(max(1, math.ceil((tomorrow - now).total_seconds())))}


async def reserve(
    db: AsyncSession,
    user: User,
    settings: Settings,
    messages: list[dict],
    request_id: UUID | None = None,
    schema: dict | None = None,
) -> AIUsage:
    """Atomically admit one provider call and hold its worst-case cost.

    Every check reads and writes persistent rows inside one transaction that holds
    the learner row lock and then the global ai:capacity row lock (row locks on
    PostgreSQL, the database write lock on SQLite), so concurrent requests from any
    number of processes are serialized and cannot overshoot a limit.
    """
    if not priced(settings):
        # No reliable tariff: refuse instead of treating the model as free.
        raise unavailable()
    await lock_learner(db, user.id)
    if request_id and await db.scalar(
        select(AIUsage.id).where(AIUsage.user_id == user.id, AIUsage.request_id == request_id)
    ):
        raise ApiError(409, "AI_REQUEST_DUPLICATE", "Request already received; reload history")
    now = utcnow()
    today = now.date()
    # Reservations of crashed workers stop blocking the learner after the lease,
    # but keep counting toward the budget until settled.
    lease_start = now - timedelta(seconds=settings.ai_request_timeout + 60)
    # Released holds (provider certainly never generated) do not use up learner quota.
    counted = func.coalesce(AIUsage.cost_source, "").notin_(("released", "refused"))
    running = (
        await db.scalar(
            select(func.count())
            .select_from(AIUsage)
            .where(
                AIUsage.user_id == user.id,
                AIUsage.status == "reserved",
                AIUsage.created_at > lease_start,
            )
        )
        or 0
    )
    if running >= settings.ai_max_concurrent_requests:
        raise ApiError(429, "AI_BUSY", "An AI request is already running")
    used_today = (
        await db.scalar(
            select(func.count())
            .select_from(AIUsage)
            .where(AIUsage.user_id == user.id, AIUsage.day == today, counted)
        )
        or 0
    )
    if used_today >= settings.ai_daily_user_limit:
        raise ApiError(
            429,
            "AI_DAILY_LIMIT",
            "Daily AI message limit reached. It resets at 00:00 UTC.",
            headers=until_next_utc_day(now),
        )
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
    input_tokens = billing.input_token_bound(
        messages, schema if settings.ai_structured_outputs else None
    )
    if input_tokens > settings.ai_max_input_tokens:
        raise ApiError(422, "AI_INPUT_LIMIT", "AI context exceeded input token limit")
    tokens = input_tokens + settings.ai_max_output_tokens
    spent = (
        await db.scalar(
            select(func.sum(AIUsage.reserved_tokens)).where(
                AIUsage.user_id == user.id, AIUsage.day == today, counted
            )
        )
        or 0
    )
    if spent + tokens > settings.ai_daily_token_budget:
        raise ApiError(429, "AI_BUDGET_LIMIT", "Daily AI budget reached")
    # Worst case: every prompt byte is a token and the reply uses max_tokens.
    cost = billing.tariff_microusd(settings, input_tokens, settings.ai_max_output_tokens)
    committed = (
        await db.scalar(
            select(func.sum(func.coalesce(AIUsage.cost_microusd, AIUsage.reserved_microusd))).where(
                AIUsage.day == today
            )
        )
        or 0
    )
    if committed + cost > billing.budget_microusd(settings):
        # Global spend is not disclosed to learners.
        raise ApiError(
            429,
            "AI_BUDGET_LIMIT",
            "Fleng AI has reached its daily limit. It resets at 00:00 UTC.",
            headers=until_next_utc_day(now),
        )
    await db.execute(
        delete(AIUsage)
        .where(AIUsage.created_at < now - timedelta(days=30))
        .execution_options(synchronize_session="fetch")
    )
    usage = AIUsage(
        user_id=user.id,
        model=settings.openrouter_model,
        status="reserved",
        reserved_tokens=tokens,
        reserved_microusd=cost,
        request_id=request_id,
        day=today,
        created_at=now,
    )
    db.add(usage)
    await db.commit()
    return usage


def usage_id(usage: AIUsage) -> UUID:
    """Primary key without a lazy load, which is unavailable after a rollback."""
    identity = sa_inspect(usage).identity
    if identity is None:
        raise RuntimeError("AI usage reservation was not persisted")
    return identity[0]


def outcome(exc: BaseException) -> str | None:
    """released: nothing sent (free). refused: upstream 4xx (prompt cost only)."""
    if isinstance(exc, UpstreamRefused):
        return "refused"
    return "released" if isinstance(exc, NotBilled) else None


def charge_values(settings: Settings, usage_info: dict | None, state: str | None = None) -> dict:
    """Final charge columns: release, refusal, provider cost, tariff x tokens, or the hold."""
    if state == "released":
        return {"cost_microusd": 0, "cost_source": "released"}
    if state == "refused":
        # Hold minus the output part; SQL expression because rolled-back ORM
        # objects cannot be lazily refreshed in async sessions.
        output = billing.tariff_microusd(settings, 0, settings.ai_max_output_tokens)
        return {
            "cost_microusd": case(
                (AIUsage.reserved_microusd > output, AIUsage.reserved_microusd - output),
                else_=0,
            ),
            "cost_source": "refused",
        }
    charge = billing.settled_charge(settings, usage_info)
    if charge is None:
        # Unknown cost: the conservative reservation becomes the charge.
        return {"cost_microusd": AIUsage.reserved_microusd, "cost_source": "reserved"}
    return {"cost_microusd": charge[0], "cost_source": charge[1]}


async def finish_usage(
    db: AsyncSession,
    usage: AIUsage,
    settings: Settings,
    result: Completion | None,
    *,
    usage_info: dict | None = None,
    state: str | None = None,
) -> None:
    """Settle a reservation; only pre-generation failures release or reduce it."""
    info = result.usage if result else usage_info
    await db.execute(
        update(AIUsage)
        .where(AIUsage.id == usage_id(usage))
        .values(
            status="completed" if result else "failed",
            usage=info or None,
            **charge_values(settings, info, state),
        )
    )
    await db.commit()


async def save_turn(
    db: AsyncSession,
    user: User,
    conversation: AIConversation | None,
    payload: ChatRequest,
    result: Completion,
    usage: AIUsage,
    settings: Settings,
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
    # History and the settled charge commit together.
    await db.execute(
        update(AIUsage)
        .where(AIUsage.id == usage_id(usage))
        .values(
            status="completed",
            usage=result.usage or None,
            **charge_values(settings, result.usage),
        )
    )
    await db.commit()
    await db.refresh(answer)
    return conversation, answer


async def chat(
    db: AsyncSession, user: User, payload: ChatRequest, settings: Settings, provider: Provider
):
    conversation, messages = await prepare_chat(db, user, payload, settings)
    usage = await reserve(db, user, settings, messages, payload.request_id)
    state: str | None = "released"
    try:
        async with capacity(settings):
            state = None
            async with asyncio.timeout(settings.ai_request_timeout):
                result = await provider.complete(messages)
    except BaseException as exc:
        await db.rollback()
        await finish_usage(db, usage, settings, None, state=outcome(exc) or state)
        raise
    try:
        return await save_turn(db, user, conversation, payload, result, usage, settings)
    except BaseException:
        # The provider answered: charge its reported cost even if saving failed.
        await db.rollback()
        await finish_usage(db, usage, settings, None, usage_info=result.usage)
        raise


async def structured(
    db: AsyncSession,
    user: User,
    payload: ExplainRequest | GenerateRequest,
    settings: Settings,
    provider: Provider,
):
    lesson_id = payload.lesson_id if isinstance(payload, ExplainRequest) else None
    extra = {}
    schema_type: type[Explanation] | type[GeneratedExercise]
    if isinstance(payload, ExplainRequest):
        validate_input(payload.student_answer, settings)
        validate_input(payload.topic, settings)
        if payload.exercise_id:
            exercise = await db.get(Exercise, payload.exercise_id)
            if exercise is None or (lesson_id and lesson_id != exercise.lesson_id):
                raise ApiError(404, "NOT_FOUND", "Exercise not found")
            lesson_id = exercise.lesson_id
            extra["exercise_prompt"] = exercise.prompt[:2000]
            # Official answer keys are deliberately excluded.
        schema_type, task = Explanation, "explain"
    else:
        validate_input(payload.topic, settings)
        schema_type, task = GeneratedExercise, "generate"
    if lesson_id:
        await context.lesson_context(db, lesson_id)
    learner = await context.learner_context(db, user, lesson_id)
    if isinstance(payload, GenerateRequest) and payload.level:
        learner["level"] = payload.level
    learner.update(extra)
    schema = schema_type.model_json_schema(by_alias=False)
    request = json.dumps(payload.model_dump(mode="json", exclude_none=True))
    messages = prompts.messages(learner, request, task=task, schema=schema)
    usage = await reserve(db, user, settings, messages, schema=schema)
    result = None
    state: str | None = "released"
    try:
        async with capacity(settings):
            state = None
            async with asyncio.timeout(settings.ai_request_timeout):
                result = await provider.complete(messages, schema)
        parsed = schema_type.model_validate_json(result.content)
        if isinstance(payload, GenerateRequest) and (
            not isinstance(parsed, GeneratedExercise) or parsed.type != payload.exercise_type
        ):
            raise ValueError("Exercise type mismatch")
        await finish_usage(db, usage, settings, result)
        return parsed
    except (ValidationError, ValueError) as exc:
        info = result.usage if result else None
        await finish_usage(db, usage, settings, None, usage_info=info)
        raise ApiError(
            502, "AI_INVALID_RESPONSE", "AI returned invalid practice material"
        ) from exc
    except BaseException as exc:
        await db.rollback()
        await finish_usage(db, usage, settings, None, state=outcome(exc) or state)
        raise
