"""Server-side AI quotas and the global OpenRouter budget.

A file-backed SQLite database with one engine per simulated worker exercises the
real cross-connection locking; no in-process state is shared between "workers".
Provider calls use fakes or httpx.MockTransport only, never paid requests.
"""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from itertools import count

import httpx
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from app.core.config import Settings, get_settings
from app.db.base import Base
from app.db.models import AIMessage, AIUsage, User
from app.db.session import get_db
from app.main import app
from app.modules.ai import billing, service
from app.modules.ai.provider import Completion, OpenRouterProvider
from app.modules.ai.router import provider_dependency, stream_chat
from app.modules.ai.schemas import ChatRequest
from tests.test_ai import PRICED, FakeProvider
from tests.test_learning_extensions import headers

ENABLED = {"ai_enabled": True, "openrouter_api_key": "test-only", "openrouter_model": "test/model"}
# Output-dominated tariff: one worst-case request reserves 800 * 1000 µ$ = $0.80 + input.
EXPENSIVE = {"ai_input_price_per_mtok_usd": "0", "ai_output_price_per_mtok_usd": "1000"}


def configure(**kwargs) -> Settings:
    settings = Settings(**{**ENABLED, **PRICED, "ai_requests_per_minute": 1000, **kwargs})
    app.dependency_overrides[get_settings] = lambda: settings
    return settings


class Worlds:
    """Independent engines on one database file: each behaves like a worker process."""

    def __init__(self, url: str):
        self.url = url
        self.engines: list = []
        self.factories: list = []
        self.turn = count()

    def start_worker(self) -> None:
        engine = create_async_engine(self.url, connect_args={"timeout": 30})
        self.engines.append(engine)
        self.factories.append(async_sessionmaker(engine, expire_on_commit=False))

    async def restart(self) -> None:
        """Drop every worker (and all in-memory state) and boot a fresh one."""
        for engine in self.engines:
            await engine.dispose()
        self.engines, self.factories = [], []
        self.start_worker()

    async def get_db(self):
        factories = self.factories
        async with factories[next(self.turn) % len(factories)]() as session:
            yield session

    def session(self):
        return self.factories[0]()


@pytest_asyncio.fixture
async def world(tmp_path):
    worlds = Worlds(f"sqlite+aiosqlite:///{tmp_path / 'ai.db'}")
    worlds.start_worker()
    worlds.start_worker()
    async with worlds.engines[0].begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    app.dependency_overrides[get_db] = worlds.get_db
    configure()
    yield worlds
    app.dependency_overrides.clear()
    for engine in worlds.engines:
        await engine.dispose()


@pytest_asyncio.fixture
async def http(world):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture
def fake():
    provider = FakeProvider()
    app.dependency_overrides[provider_dependency] = lambda: provider
    return provider


class Gate(FakeProvider):
    """Holds every provider call open until released, to overlap requests."""

    def __init__(self):
        super().__init__()
        self.entered = asyncio.Event()
        self.release = asyncio.Event()
        self.in_flight = self.peak = 0

    async def complete(self, messages, schema=None):
        self.requests.append(messages)
        self.in_flight += 1
        self.peak = max(self.peak, self.in_flight)
        self.entered.set()
        try:
            await self.release.wait()
        finally:
            self.in_flight -= 1
        return Completion("Done", "test/model", {"cost": 0.0001})

    async def stream(self, messages):
        self.requests.append(messages)
        self.in_flight += 1
        self.peak = max(self.peak, self.in_flight)
        self.entered.set()
        try:
            await self.release.wait()
        finally:
            self.in_flight -= 1
        yield Completion("Done", "test/model", {"cost": 0.0001})


async def rows(world, *where):
    async with world.session() as db:
        return list((await db.scalars(select(AIUsage).where(*where))).all())


def clock(monkeypatch, moment: datetime) -> None:
    monkeypatch.setattr(service, "utcnow", lambda: moment)


async def chat(http, auth, message="Hi", path="chat"):
    return await http.post(f"/api/v1/ai/{path}", headers=auth, json={"message": message})


# ── Per-learner daily quota ─────────────────────────────────────────────────


async def test_thirty_daily_messages_then_blocked(http, world, fake):
    auth = await headers(http)
    for index in range(30):
        # Alternate routes: both share the same persistent counter.
        path = "chat/stream" if index % 2 else "chat"
        response = await chat(http, auth, path=path)
        assert response.status_code == 200, index
    blocked = await chat(http, auth)
    assert blocked.status_code == 429
    error = blocked.json()["error"]
    assert error["code"] == "AI_DAILY_LIMIT"
    assert "00:00 UTC" in error["message"]
    assert int(blocked.headers["Retry-After"]) >= 1
    # Every AI endpoint consumes the same quota.
    for path, body in [
        ("chat/stream", {"message": "Hi"}),
        ("explain", {"studentAnswer": "I is"}),
        ("generate-exercise", {"topic": "verbs", "exerciseType": "fill_blank"}),
    ]:
        response = await http.post(f"/api/v1/ai/{path}", headers=auth, json=body)
        assert response.json()["error"]["code"] == "AI_DAILY_LIMIT"
    assert len(fake.requests) == 30
    # Another learner keeps a separate quota.
    assert (await chat(http, await headers(http, "second@example.com"))).status_code == 200


async def test_daily_quota_resets_at_utc_midnight(http, world, fake, monkeypatch):
    configure(ai_daily_user_limit=2)
    auth = await headers(http)
    clock(monkeypatch, datetime(2026, 11, 16, 23, 59, 30, tzinfo=UTC))
    assert (await chat(http, auth)).status_code == 200
    assert (await chat(http, auth)).status_code == 200
    blocked = await chat(http, auth)
    assert blocked.json()["error"]["code"] == "AI_DAILY_LIMIT"
    assert blocked.headers["Retry-After"] == "30"
    clock(monkeypatch, datetime(2026, 11, 16, 23, 59, 59, 999999, tzinfo=UTC))
    assert (await chat(http, auth)).status_code == 429
    clock(monkeypatch, datetime(2026, 11, 17, 0, 0, tzinfo=UTC))
    assert (await chat(http, auth)).status_code == 200
    days = sorted(str(row.day) for row in await rows(world))
    assert days == ["2026-11-16", "2026-11-16", "2026-11-17"]


async def test_budget_resets_at_utc_midnight(http, world, fake, monkeypatch):
    configure(**EXPENSIVE)
    auth = await headers(http)
    clock(monkeypatch, datetime(2026, 11, 16, 23, 0, tzinfo=UTC))
    assert (await chat(http, auth)).status_code == 200
    assert (await chat(http, auth)).json()["error"]["code"] == "AI_BUDGET_LIMIT"
    clock(monkeypatch, datetime(2026, 11, 17, 0, 0, tzinfo=UTC))
    assert (await chat(http, auth)).status_code == 200


# ── Input and output size ───────────────────────────────────────────────────


@pytest.mark.parametrize("path", ["chat", "chat/stream"])
async def test_message_length_500_allowed_501_rejected(http, world, fake, path):
    auth = await headers(http)
    assert "event: done" in (await chat(http, auth, "a" * 500, "chat/stream")).text
    assert (await chat(http, auth, "я" * 500, "chat")).status_code == 200
    rejected = await chat(http, auth, "a" * 501, path)
    assert rejected.status_code == 422
    assert rejected.json()["error"]["code"] == "AI_INPUT_LIMIT"
    explain = await http.post("/api/v1/ai/explain", headers=auth, json={"studentAnswer": "a" * 501})
    assert explain.json()["error"]["code"] == "AI_INPUT_LIMIT"
    assert len(fake.requests) == 2
    # Rejected input consumed no quota and created no reservation.
    assert len(await rows(world)) == 2
    status = await http.get("/api/v1/ai/status", headers=auth)
    assert status.json()["maxInputChars"] == 500


async def test_output_tokens_capped_and_reserved_at_800():
    sent = []

    def handler(request):
        sent.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "Hi"}, "finish_reason": "stop"}]},
        )

    settings = Settings(**ENABLED, **PRICED)
    assert settings.ai_max_output_tokens == 800
    await OpenRouterProvider(settings, httpx.MockTransport(handler)).complete(
        [{"role": "user", "content": "Hi"}]
    )
    assert sent[0]["max_tokens"] == 800
    # Endpoints pricier than the reservation tariff are excluded upstream.
    assert sent[0]["provider"]["max_price"] == {"prompt": 0.15, "completion": 0.6, "request": 0}
    with pytest.raises(ValueError):
        Settings(ai_max_output_tokens=0)


async def test_reservation_is_worst_case_cost(http, world, fake):
    settings = configure()
    gate = Gate()
    app.dependency_overrides[provider_dependency] = lambda: gate
    auth = await headers(http)
    task = asyncio.create_task(chat(http, auth, "Hello there"))
    await asyncio.wait_for(gate.entered.wait(), 5)
    (held,) = await rows(world)
    assert held.status == "reserved" and held.cost_microusd is None
    input_bound = billing.input_token_bound(gate.requests[0])
    assert held.reserved_tokens == input_bound + 800
    assert held.reserved_microusd == billing.tariff_microusd(settings, input_bound, 800)
    gate.release.set()
    assert (await task).status_code == 200
    (settled,) = await rows(world)
    assert (settled.cost_microusd, settled.cost_source) == (100, "provider")


# ── Global budget ───────────────────────────────────────────────────────────


async def test_daily_budget_exceeded(http, world, fake):
    configure(**EXPENSIVE)
    auth = await headers(http)
    assert (await chat(http, auth)).status_code == 200
    blocked = await chat(http, await headers(http, "other@example.com"))
    assert blocked.status_code == 429
    error = blocked.json()["error"]
    assert error["code"] == "AI_BUDGET_LIMIT"
    # No internal amounts or provider details reach the learner.
    assert "$" not in blocked.text and "usd" not in blocked.text.lower()
    assert "openrouter" not in blocked.text.lower()
    assert len(fake.requests) == 1


async def test_settled_actual_cost_frees_unused_reservation(http, world, fake):
    configure(**EXPENSIVE)
    auth = await headers(http)

    async def cheap(messages, schema=None):
        fake.requests.append(messages)
        return Completion("Hi", "test/model", {"cost": 0.05})

    fake.complete = cheap
    # $0.80 is held per call, but only $0.05 is charged, so several calls fit in $1.
    for _ in range(3):
        assert (await chat(http, auth)).status_code == 200
    assert [r.cost_microusd for r in await rows(world)] == [50000] * 3


async def test_actual_cost_above_estimate_is_recorded(http, world, fake):
    configure(**EXPENSIVE)
    auth = await headers(http)

    async def pricey(messages, schema=None):
        return Completion("Hi", "test/model", {"cost": 0.95})

    fake.complete = pricey
    assert (await chat(http, auth)).status_code == 200
    (row,) = await rows(world)
    assert row.cost_microusd == 950000 > row.reserved_microusd
    assert (await chat(http, auth)).json()["error"]["code"] == "AI_BUDGET_LIMIT"


@pytest.mark.parametrize("path", ["chat", "chat/stream"])
@pytest.mark.parametrize("stagger_last", [False, True], ids=["together", "staggered"])
async def test_parallel_users_cannot_overspend_nearly_exhausted_budget(
    http, world, path, stagger_last
):
    configure(ai_concurrency=10, **EXPENSIVE)
    gate = Gate()
    app.dependency_overrides[provider_dependency] = lambda: gate
    users = [await headers(http, f"user{i}@example.com") for i in range(5)]
    async with world.session() as db:
        first = await db.scalar(select(User))
        # $0.15 already charged today: exactly one $0.80 reservation still fits.
        db.add(
            AIUsage(
                user_id=first.id,
                model="test/model",
                status="completed",
                reserved_tokens=1,
                reserved_microusd=150000,
                cost_microusd=150000,
                cost_source="provider",
            )
        )
        await db.commit()
    completed = asyncio.Queue()
    last_arrival = asyncio.Event()

    async def contender(index, auth):
        if stagger_last and index == len(users) - 1:
            await last_arrival.wait()
        response = await chat(http, auth, path=path)
        completed.put_nowait(response)
        return response

    tasks = [asyncio.create_task(contender(index, auth)) for index, auth in enumerate(users)]
    try:
        # Keep the winning reservation open until every competitor has been
        # rejected. A sleep cannot ensure this: settlement frees unused budget,
        # so late arrivals may legitimately succeed after the winner finishes.
        async with asyncio.timeout(5):
            await gate.entered.wait()
            for index in range(len(users) - 1):
                response = await completed.get()
                assert response.status_code == 429
                assert response.json()["error"]["code"] == "AI_BUDGET_LIMIT"
                if index == len(users) - 3:
                    last_arrival.set()
        assert len(gate.requests) == 1
        held = await rows(world)
        assert sorted(r.status for r in held) == ["completed", "reserved"]
        # Settled spend PLUS the active reservation, across both connections.
        assert (
            sum(
                r.cost_microusd if r.cost_microusd is not None else r.reserved_microusd
                for r in held
            )
            == 950000
            <= 1_000_000
