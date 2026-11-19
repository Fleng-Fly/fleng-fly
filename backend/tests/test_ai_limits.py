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
        )
    finally:
        # Also release a deliberately delayed contender on assertion/timeout,
        # and drain all tasks before the fixture disposes its database engines.
        last_arrival.set()
        gate.release.set()
        responses = await asyncio.gather(*tasks, return_exceptions=True)
    assert all(isinstance(response, httpx.Response) for response in responses)
    assert sorted(r.status_code for r in responses) == [200] + [429] * 4
    if path == "chat/stream":
        winner = next(r for r in responses if r.status_code == 200)
        assert "event: done\n" in winner.text
        assert "event: error\n" not in winner.text
    settled = await rows(world)
    assert all(r.status == "completed" for r in settled)
    assert sum(r.cost_microusd for r in settled) == 150100 <= 1_000_000

    # The other valid schedule: once $0.80 settles at $0.0001, a late
    # contender/retry may reserve $0.80 again without exceeding the $1 budget.
    assert (await chat(http, users[-1], path=path)).status_code == 200
    assert len(gate.requests) == 2
    assert sum(r.cost_microusd for r in await rows(world)) == 150200 <= 1_000_000


# ── Concurrency per learner ─────────────────────────────────────────────────


@pytest.mark.parametrize("second_path", ["chat", "chat/stream", "explain"])
async def test_parallel_requests_of_one_user(http, world, second_path):
    gate = Gate()
    app.dependency_overrides[provider_dependency] = lambda: gate
    auth = await headers(http)
    first = asyncio.create_task(chat(http, auth))
    await asyncio.wait_for(gate.entered.wait(), 5)
    # Routed to the other worker/engine: only the database can know about `first`.
    body = {"studentAnswer": "I is"} if second_path == "explain" else {"message": "Hi"}
    second = await http.post(f"/api/v1/ai/{second_path}", headers=auth, json=body)
    assert second.status_code == 429
    assert second.json()["error"]["code"] == "AI_BUSY"
    gate.release.set()
    assert (await first).status_code == 200
    assert len(gate.requests) == 1
    # The slot is free again once the first request settles.
    gate.complete = FakeProvider().complete
    assert (await chat(http, auth)).status_code == 200


async def test_burst_of_parallel_requests_admits_one(http, world):
    gate = Gate()
    app.dependency_overrides[provider_dependency] = lambda: gate
    auth = await headers(http)
    tasks = [asyncio.create_task(chat(http, auth, path=p)) for p in ["chat", "chat/stream"] * 4]
    await asyncio.wait_for(gate.entered.wait(), 5)
    await asyncio.sleep(0.2)
    gate.release.set()
    responses = await asyncio.gather(*tasks)
    # Late arrivals may legitimately run after the first settles; overlap never happens.
    assert gate.peak == 1
    busy = [r for r in responses if "AI_BUSY" in r.text]
    assert busy and len(busy) + len(gate.requests) == 8
    # Rejected attempts do not burn daily quota: one row per provider call.
    counted = [r for r in await rows(world) if r.cost_source != "released"]
    assert len(counted) == len(gate.requests)


# ── Provider failures and settlement ────────────────────────────────────────


def openrouter(handler) -> OpenRouterProvider:
    provider = OpenRouterProvider(
        app.dependency_overrides[get_settings](), httpx.MockTransport(handler)
    )
    app.dependency_overrides[provider_dependency] = lambda: provider
    return provider


def stream_body(usage: dict | None) -> str:
    frames = [{"choices": [{"delta": {"content": "Hello"}, "finish_reason": "stop"}]}]
    if usage is not None:
        frames.append({"choices": [], "usage": usage})
    return "".join("data: " + json.dumps(f) + "\n\n" for f in frames) + "data: [DONE]\n\n"


@pytest.mark.parametrize("path", ["chat", "chat/stream"])
@pytest.mark.parametrize(
    "status,code,source",
    [
        # 4xx: nothing generated, but OpenRouter documents possible prompt charges.
        (400, "AI_UNAVAILABLE", "refused"),
        (401, "AI_UNAVAILABLE", "refused"),
        (402, "AI_UNAVAILABLE", "refused"),
        (404, "AI_UNAVAILABLE", "refused"),  # e.g. no endpoint within max_price
        (429, "AI_RATE_LIMITED", "refused"),
        (408, "AI_UNAVAILABLE", "reserved"),
        (500, "AI_UNAVAILABLE", "reserved"),
        (502, "AI_UNAVAILABLE", "reserved"),
    ],
)
async def test_openrouter_errors_charge_by_certainty(http, world, path, status, code, source):
    openrouter(lambda request: httpx.Response(status, text="upstream details sk-or-secret"))
    auth = await headers(http)
    response = await chat(http, auth, path=path)
    assert "sk-or-secret" not in response.text
    if path == "chat":
        assert response.json()["error"]["code"] == code
    else:
        assert f'"code": "{code}"' in response.text
    (row,) = await rows(world)
    assert (row.status, row.cost_source) == ("failed", source)
    if source == "reserved":
        # The model may have run: keep the worst-case hold as the charge.
        assert row.cost_microusd == row.reserved_microusd
    else:
        # Output cost is freed; the prompt cost stays booked and quota is not used.
        assert 0 < row.cost_microusd < row.reserved_microusd
        assert row.reserved_microusd - row.cost_microusd == billing.tariff_microusd(
            Settings(**ENABLED, **PRICED), 0, 800
        )


@pytest.mark.parametrize(
    "error,released",
    [
        (httpx.ConnectError("refused"), True),
        (httpx.ConnectTimeout("connect"), True),
        (httpx.ReadTimeout("read"), False),
        (httpx.RemoteProtocolError("reset"), False),
    ],
)
async def test_transport_failures(http, world, error, released):
    def handler(request):
        raise error

    openrouter(handler)
    auth = await headers(http)
    assert (await chat(http, auth)).status_code in (503, 504)
    (row,) = await rows(world)
    assert row.cost_source == ("released" if released else "reserved")


@pytest.mark.parametrize("path", ["chat", "chat/stream"])
@pytest.mark.parametrize(
    "usage,source",
    [
        ({"prompt_tokens": 1000, "completion_tokens": 100, "cost": 0.0123}, "provider"),
        ({"prompt_tokens": 1000, "completion_tokens": 100}, "tariff"),
        ({"total_tokens": 1100}, "reserved"),
        (None, "reserved"),
        ({"cost": "free", "prompt_tokens": "many"}, "reserved"),
    ],
)
async def test_cost_settlement_sources(http, world, path, usage, source):
    def handler(request):
        if json.loads(request.content)["stream"]:
            return httpx.Response(200, text=stream_body(usage))
        body = {"choices": [{"message": {"content": "Hello"}, "finish_reason": "stop"}]}
        if usage is not None:
            body["usage"] = usage
        return httpx.Response(200, json=body)

    openrouter(handler)
    auth = await headers(http)
    response = await chat(http, auth, path=path)
    assert response.status_code == 200
    (row,) = await rows(world)
    assert row.status == "completed" and row.cost_source == source
    expected = {
        "provider": 12300,
        # 1000 * 0.15 + 100 * 0.60 micro-USD at the configured tariff.
        "tariff": 210,
        "reserved": row.reserved_microusd,
    }[source]
    assert row.cost_microusd == expected


@pytest.mark.parametrize(
    "overrides",
    [
        {"ai_input_price_per_mtok_usd": None},
        {"ai_output_price_per_mtok_usd": None},
        {"openrouter_model": "openrouter/auto"},
        {"openrouter_model": "openai/gpt-4o-mini:online"},
    ],
)
async def test_unknown_price_refuses_before_provider(http, world, overrides):
    configure(**overrides)
    calls = []
    openrouter(lambda request: calls.append(request) or httpx.Response(500))
    auth = await headers(http)
    assert (await http.get("/api/v1/ai/status", headers=auth)).json()["available"] is False
    for path in ["chat", "chat/stream"]:
        response = await chat(http, auth, path=path)
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "AI_UNAVAILABLE"
    assert calls == [] and await rows(world) == []


# ── SSE disconnect / cancellation ───────────────────────────────────────────


class Disconnecting:
    def __init__(self, after: int):
        self.calls, self.after = 0, after

    async def is_disconnected(self):
        self.calls += 1
        return self.calls > self.after


@pytest.mark.parametrize(
    "usage,source", [(None, "reserved"), ({"cost": 0.002, "prompt_tokens": 9}, "provider")]
)
async def test_sse_disconnect_keeps_hold_unless_cost_is_known(http, world, usage, source):
    settings = configure()
    await headers(http)

    class Provider(FakeProvider):
        async def stream(self, messages):
            yield Completion("partial", "test/model")
            if usage:
                yield Completion("", "test/model", usage)
            yield Completion(" more", "test/model")

    async with world.session() as db:
        user = await db.scalar(select(User).options(selectinload(User.profile)))
        response = await stream_chat(
            payload=ChatRequest(message="Hi"),
            request=Disconnecting(after=2 if usage else 1),
            user=user,
            db=db,
            settings=settings,
            provider=Provider(),
        )
        chunks = [chunk async for chunk in response.body_iterator]
    assert "event: done" not in "".join(chunks)
    (row,) = await rows(world)
    assert row.status == "failed" and row.cost_source == source
    if source == "reserved":
        assert row.cost_microusd == row.reserved_microusd > 0
    async with world.session() as db:
        assert await db.scalar(select(func.count()).select_from(AIMessage)) == 0


async def test_sse_cancel_mid_stream_keeps_hold(http, world):
    settings = configure()
    await headers(http)
    waiting = asyncio.Event()

    class Connected:
        async def is_disconnected(self):
            return False

    class Hanging(FakeProvider):
        async def stream(self, messages):
            yield Completion("partial", "test/model")
            waiting.set()
            await asyncio.Event().wait()

    async with world.session() as db:
        user = await db.scalar(select(User).options(selectinload(User.profile)))
        response = await stream_chat(
            payload=ChatRequest(message="Hi"),
            request=Connected(),
            user=user,
            db=db,
            settings=settings,
            provider=Hanging(),
        )

        async def consume():
            async for _ in response.body_iterator:
                pass

        task = asyncio.create_task(consume())
        await asyncio.wait_for(waiting.wait(), 5)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    (row,) = await rows(world)
    assert row.status == "failed"
    assert (row.cost_microusd, row.cost_source) == (row.reserved_microusd, "reserved")


# ── Restart / multiple processes ────────────────────────────────────────────


async def test_limits_survive_restart(http, world, fake, monkeypatch):
    configure(ai_daily_user_limit=3)
    auth = await headers(http)
    for _ in range(3):
        assert (await chat(http, auth, path="chat/stream")).status_code == 200
    await world.restart()
    # Fresh worker, no shared memory: quota and spend come from the database.
    assert (await chat(http, auth)).json()["error"]["code"] == "AI_DAILY_LIMIT"
    other = await headers(http, "fresh@example.com")
    async with world.session() as db:
        # A worker crashed mid-request: its hold was never settled.
        crashed = await db.scalar(select(User).where(User.email == "fresh@example.com"))
        db.add(
            AIUsage(
                user_id=crashed.id,
                model="test/model",
                status="reserved",
                reserved_tokens=1,
                reserved_microusd=999000,
                created_at=datetime.now(UTC) - timedelta(hours=1),
            )
        )
        await db.commit()
    await world.restart()
    # The stale lease no longer blocks the learner, but its cost still counts.
    response = await chat(http, other)
    assert response.json()["error"]["code"] == "AI_BUDGET_LIMIT"
    configure(ai_daily_user_limit=3, ai_daily_budget_usd="2.00")
    assert (await chat(http, other)).status_code == 200


# ── Audit regressions ───────────────────────────────────────────────────────


def raw_write_is_free(path: str) -> bool:
    """A second connection can take the SQLite write lock right now (0.2 s wait)."""
    import sqlite3

    connection = sqlite3.connect(path, timeout=0.2, isolation_level=None)
    try:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("UPDATE request_limits SET count = count WHERE 0")
        connection.execute("COMMIT")
        return True
    except sqlite3.OperationalError:
        return False
    finally:
        connection.close()


@pytest.mark.parametrize("path", ["chat", "chat/stream"])
async def test_no_write_lock_held_while_waiting_for_provider(http, world, path):
    gate = Gate()
    app.dependency_overrides[provider_dependency] = lambda: gate
    auth = await headers(http)
    task = asyncio.create_task(chat(http, auth, path=path))
    await asyncio.wait_for(gate.entered.wait(), 5)
    db_file = world.url.removeprefix("sqlite+aiosqlite:///")
    # Provider wait (and, for SSE, the open response) must not pin the database.
    assert await asyncio.to_thread(raw_write_is_free, db_file)
    gate.release.set()
    assert (await task).status_code == 200


async def test_no_write_lock_held_mid_sse_stream(http, world):
    settings = configure()
    await headers(http)
    waiting = asyncio.Event()

    class Connected:
        async def is_disconnected(self):
            return False

    class Hanging(FakeProvider):
        async def stream(self, messages):
            yield Completion("partial", "test/model")
            waiting.set()
            await asyncio.Event().wait()

    async with world.session() as db:
        user = await db.scalar(select(User).options(selectinload(User.profile)))
        response = await stream_chat(
            payload=ChatRequest(message="Hi"),
            request=Connected(),
            user=user,
            db=db,
            settings=settings,
            provider=Hanging(),
        )

        async def consume():
            async for _ in response.body_iterator:
                pass

        task = asyncio.create_task(consume())
        await asyncio.wait_for(waiting.wait(), 5)
        assert await asyncio.to_thread(
            raw_write_is_free, world.url.removeprefix("sqlite+aiosqlite:///")
        )
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task


async def test_cancelled_non_stream_request_keeps_hold(http, world):
    settings = configure()
    gate = Gate()
    await headers(http)
    async with world.session() as db:
        user = await db.scalar(select(User).options(selectinload(User.profile)))
        task = asyncio.create_task(
            service.chat(db, user, ChatRequest(message="Hi"), settings, gate)
        )
        await asyncio.wait_for(gate.entered.wait(), 5)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    (row,) = await rows(world)
    assert row.status == "failed"
    assert (row.cost_microusd, row.cost_source) == (row.reserved_microusd, "reserved")


async def test_stale_unsettled_hold_does_not_block_next_utc_day(http, world, fake, monkeypatch):
    """A crashed worker's hold only ever counts for the day it was made."""
    configure(ai_daily_user_limit=1, **EXPENSIVE)
    auth = await headers(http)
    async with world.session() as db:
        user = await db.scalar(select(User))
        db.add(
            AIUsage(
                user_id=user.id,
                model="test/model",
                status="reserved",
                reserved_tokens=1,
                reserved_microusd=1_000_000,
                created_at=datetime(2026, 11, 16, 12, 0, tzinfo=UTC),
                day=datetime(2026, 11, 16).date(),
            )
        )
        await db.commit()
    clock(monkeypatch, datetime(2026, 11, 16, 12, 30, tzinfo=UTC))
    assert (await chat(http, auth)).status_code == 429  # budget and lease: same day
    clock(monkeypatch, datetime(2026, 11, 17, 0, 0, 1, tzinfo=UTC))
    assert (await chat(http, auth)).status_code == 200


async def test_failed_settlement_write_cannot_outlive_the_day(http, world, fake, monkeypatch):
    """Even if settlement never happens, quota and budget recover at 00:00 UTC."""
    configure(ai_daily_user_limit=30, **EXPENSIVE)
    auth = await headers(http)
    real, real_save = service.finish_usage, service.save_turn

    async def broken(*args, **kwargs):
        raise RuntimeError("settlement lost")

    monkeypatch.setattr(service, "finish_usage", broken)
    monkeypatch.setattr(service, "save_turn", broken)
    clock(monkeypatch, datetime(2026, 11, 16, 20, 0, tzinfo=UTC))
    with pytest.raises(RuntimeError):
        await chat(http, auth)
    monkeypatch.setattr(service, "finish_usage", real)
    monkeypatch.setattr(service, "save_turn", real_save)
    (row,) = await rows(world)
    assert row.status == "reserved"
    clock(monkeypatch, datetime(2026, 11, 16, 20, 5, tzinfo=UTC))
    assert (await chat(http, auth)).status_code == 429
    clock(monkeypatch, datetime(2026, 11, 17, 0, 0, tzinfo=UTC))
    assert (await chat(http, auth)).status_code == 200


def test_default_token_budget_never_preempts_daily_message_quota():
    """Regression: 100000 cut the 30-message quota to ~4-24 requests per day."""
    defaults = Settings()
    worst = defaults.ai_max_input_tokens + defaults.ai_max_output_tokens
    assert defaults.ai_daily_token_budget >= defaults.ai_daily_user_limit * worst


async def test_long_history_does_not_exhaust_quota_early(http, world, fake):
    auth = await headers(http)
    first = await chat(http, auth, "a" * 500)
    cid = first.json()["conversationId"]
    for _ in range(9):
        body = {"message": "b" * 500, "conversationId": cid}
        assert (await http.post("/api/v1/ai/chat", headers=auth, json=body)).status_code == 200


@pytest.mark.parametrize("path", ["chat", "chat/stream", "explain", "generate-exercise"])
async def test_all_transports_reserve_before_local_capacity(http, world, fake, monkeypatch, path):
    original = service.reserve
    admissions = []

    async def checked_reserve(*args, **kwargs):
        # Waiting for database locks must never occupy a provider slot.
        assert service._active == 0
        admissions.append(path)
        return await original(*args, **kwargs)

    monkeypatch.setattr(service, "reserve", checked_reserve)
    payload = {"message": "Hi"}
    if path == "explain":
        payload = {"studentAnswer": "I is"}
        fake.content = json.dumps({"explanation": "Use am", "correctExample": "I am", "rule": "be"})
    elif path == "generate-exercise":
        payload = {"topic": "be", "exerciseType": "fill_blank"}
        fake.content = json.dumps(
            {"type": "fill_blank", "prompt": "I ___ here", "answer": "am", "explanation": "be"}
        )
    response = await http.post("/api/v1/ai/" + path, headers=await headers(http), json=payload)
    assert response.status_code == 200, response.text
    assert admissions == [path]
    assert len(fake.requests) == 1


async def test_refused_settlement_is_portable_and_never_negative(db_session):
    from sqlalchemy import update
    from sqlalchemy.dialects import postgresql

    from app.modules.auth.service import register_user

    user = await register_user(
        db_session, email="settlement@example.com", password="test-password", display_name="Test"
    )
    values = service.charge_values(Settings(**ENABLED, **PRICED), None, "refused")
    statement = update(AIUsage).values(**values)
    sql = str(statement.compile(dialect=postgresql.dialect()))
    assert "CASE WHEN" in sql and "max(" not in sql
    for reserved, expected in [(1000, 520), (10, 0)]:
        row = AIUsage(
            user_id=user.id, model="test/model", reserved_tokens=1, reserved_microusd=reserved
        )
        db_session.add(row)
        await db_session.flush()
        await db_session.execute(statement.where(AIUsage.id == row.id))
        await db_session.refresh(row)
        assert row.cost_microusd == expected
        assert row.cost_source == "refused"


# ── Auto Router: budget enforcement and settlement ──────────────────────────

AUTO = {"openrouter_model": "openrouter/auto", "ai_allow_auto_router": True}


def auto_body(usage, model="anthropic/claude-3.5-haiku"):
    body = {"model": model, "choices": [{"message": {"content": "Hello"}, "finish_reason": "stop"}]}
    if usage is not None:
        body["usage"] = usage
    return body


@pytest.mark.parametrize(
    "usage,source",
    [
        ({"prompt_tokens": 1000, "completion_tokens": 100, "cost": 0.0123}, "provider"),
        # Missing / partial usage: the routed model's price is unknown, so the whole
        # worst-case hold (at the configured ceiling) is charged. Never zero, never a guess.
        ({"prompt_tokens": 1000, "completion_tokens": 100}, "reserved"),
        (None, "reserved"),
    ],
)
async def test_auto_router_settlement(http, world, usage, source):
    configure(**AUTO)
    openrouter(lambda request: httpx.Response(200, json=auto_body(usage)))
    auth = await headers(http)
    assert (await http.get("/api/v1/ai/status", headers=auth)).json()["available"] is True
    assert (await chat(http, auth)).status_code == 200
    (row,) = await rows(world)
    assert row.status == "completed" and row.cost_source == source
    assert row.cost_microusd == (12300 if source == "provider" else row.reserved_microusd)
    assert row.reserved_microusd > 0


async def test_auto_router_records_the_routed_model(http, world):
    configure(**AUTO)
    openrouter(lambda request: httpx.Response(200, json=auto_body({"cost": 0.0001})))
    auth = await headers(http)
    assert (await chat(http, auth)).status_code == 200
    async with world.session() as session:
        models = set((await session.scalars(select(AIMessage.model))).all())
    assert "anthropic/claude-3.5-haiku" in models


async def test_auto_router_hold_uses_the_ceiling_and_blocks_when_over_budget(http, world):
    # Ceiling $1000/Mtok output * 800 tokens = $0.80 per hold; budget $1.00 admits one only.
    configure(**AUTO, **EXPENSIVE, ai_daily_budget_usd="1.00")
    calls = []
    openrouter(lambda r: calls.append(r) or httpx.Response(200, json=auto_body(None)))
    auth = await headers(http)
    assert (await chat(http, auth)).status_code == 200  # charged the full $0.80 hold
    second = await chat(http, auth)
    assert second.status_code == 429 and second.json()["error"]["code"] == "AI_BUDGET_LIMIT"
    assert len(calls) == 1


async def test_auto_router_actual_cost_above_the_hold_is_still_counted(http, world):
    configure(**AUTO, ai_daily_budget_usd="1.00")
    openrouter(lambda request: httpx.Response(200, json=auto_body({"cost": 5.0})))
    auth = await headers(http)
    assert (await chat(http, auth)).status_code == 200
    (row,) = await rows(world)
    assert (row.cost_microusd, row.cost_source) == (5_000_000, "provider")
    again = await chat(http, auth)
    assert again.status_code == 429 and again.json()["error"]["code"] == "AI_BUDGET_LIMIT"


@pytest.mark.parametrize("status", [429, 500])
async def test_auto_router_upstream_errors_do_not_leak_or_over_charge(http, world, status):
    configure(**AUTO)
    openrouter(lambda request: httpx.Response(status, text="Bearer test-only leaked"))
    auth = await headers(http)
    response = await chat(http, auth)
    assert response.status_code in (429, 503)
    assert "leaked" not in response.text and "test-only" not in response.text
    (row,) = await rows(world)
    assert row.cost_microusd <= row.reserved_microusd


async def test_auto_router_still_refused_without_the_opt_in(http, world):
    configure(openrouter_model="openrouter/auto")
    calls = []
    openrouter(lambda r: calls.append(r) or httpx.Response(500))
    auth = await headers(http)
    status = (await http.get("/api/v1/ai/status", headers=auth)).json()
    assert status["available"] is False and status["reason"] == "auto_router_not_enabled"
    assert (await chat(http, auth)).status_code == 503 and calls == []


# ── Auto Router: final billing-safety audit cases ───────────────────────────


async def test_auto_hold_covers_system_prompt_history_and_the_full_output_cap(http, world):
    settings = configure(**AUTO)
    gate = Gate()
    app.dependency_overrides[provider_dependency] = lambda: gate
    auth = await headers(http)
    gate.release.set()
    first = await chat(http, auth, "Explain the past simple, please.")
    conversation = first.json()["conversationId"]
    gate.release.clear()
    gate.entered.clear()
    second = asyncio.create_task(
        http.post(
            "/api/v1/ai/chat",
            headers=auth,
            json={"message": "And the present perfect?", "conversationId": conversation},
        )
    )
    await asyncio.wait_for(gate.entered.wait(), 5)
    sent = gate.requests[-1]
    roles = [m["role"] for m in sent]
    # System prompt + saved history (user and assistant) + the new message are all billed input.
    assert roles[0] == "system" and roles.count("assistant") >= 1 and roles[-1] == "user"
    held = [r for r in await rows(world) if r.status == "reserved"]
    assert len(held) == 1
    bound = billing.input_token_bound(sent)
    assert bound >= sum(len(m["content"].encode()) for m in sent)
    assert held[0].reserved_tokens == bound + settings.ai_max_output_tokens == bound + 800
    assert held[0].reserved_microusd == billing.tariff_microusd(settings, bound, 800)
    gate.release.set()
    assert (await second).status_code == 200


def test_ceiling_units_match_provider_max_price_and_the_hold():
    from app.modules.ai.provider import max_price

    settings = Settings(**{**ENABLED, **AUTO, **EXPENSIVE, "ai_input_price_per_mtok_usd": "2.5"})
    ceiling = max_price(settings)
    # USD per million tokens in both places: 1M input tokens cost exactly the ceiling in USD.
    assert ceiling == {"prompt": 2.5, "completion": 1000.0, "request": 0}
    assert billing.tariff_microusd(settings, 1_000_000, 0) == 2_500_000
    assert billing.tariff_microusd(settings, 0, 1_000_000) == 1_000_000_000
    # The most one request can ever be admitted for: a full input window plus 800 output tokens.
    worst = billing.tariff_microusd(settings, settings.ai_max_input_tokens, 800)
    assert worst == 24000 * 2.5 + 800 * 1000


@pytest.mark.parametrize(
    "usage",
    [
        {"cost": -1},
        {"cost": True},
        {"cost": 1e13},
        {"cost": "0.0001"},
        {"cost": None},
    ],
)
@pytest.mark.parametrize("path", ["chat", "chat/stream"])
async def test_auto_untrustworthy_cost_charges_the_full_hold_not_zero(http, world, usage, path):
    configure(**AUTO)

    def handler(request):
        if json.loads(request.content)["stream"]:
            frames = [
                {"choices": [{"delta": {"content": "Hi"}, "finish_reason": "stop"}]},
                {"choices": [], "usage": usage},
            ]
            text = "".join("data: " + json.dumps(f) + "\n\n" for f in frames) + "data: [DONE]\n\n"
            return httpx.Response(200, text=text)
        return httpx.Response(200, json=auto_body(usage))

    openrouter(handler)
    auth = await headers(http)
    assert (await chat(http, auth, path=path)).status_code == 200
    (row,) = await rows(world)
    assert row.cost_source == "reserved"
    assert row.cost_microusd == row.reserved_microusd > 0


@pytest.mark.parametrize("path", ["chat", "chat/stream"])
async def test_auto_tokens_without_cost_never_priced_by_the_ceiling(http, world, path):
    configure(**AUTO)

    def handler(request):
        usage = {"prompt_tokens": 10, "completion_tokens": 5}
        if json.loads(request.content)["stream"]:
            return httpx.Response(200, text=stream_body(usage))
        return httpx.Response(200, json=auto_body(usage))

    openrouter(handler)
    auth = await headers(http)
    assert (await chat(http, auth, path=path)).status_code == 200
    (row,) = await rows(world)
    assert row.cost_source == "reserved" and row.cost_microusd == row.reserved_microusd


async def test_auto_parallel_users_cannot_overbook_the_daily_budget(http, world):
    configure(ai_concurrency=10, **AUTO, **EXPENSIVE)  # one hold = $0.80 + input
    gate = Gate()
    app.dependency_overrides[provider_dependency] = lambda: gate
    users = [await headers(http, f"auto{i}@example.com") for i in range(6)]
    tasks = [asyncio.create_task(chat(http, auth)) for auth in users]
    try:
        async with asyncio.timeout(5):
            await gate.entered.wait()
            await asyncio.sleep(0.3)  # every competitor has been decided while the hold is open
        held = await rows(world)
        assert len(gate.requests) == 1 and [r.status for r in held] == ["reserved"]
        assert sum(r.reserved_microusd for r in held) <= 1_000_000
    finally:
        gate.release.set()
        responses = await asyncio.gather(*tasks)
    codes = sorted(r.status_code for r in responses)
    assert codes.count(200) == 1 and codes.count(429) == 5
    assert {r.json()["error"]["code"] for r in responses if r.status_code == 429} == {
        "AI_BUDGET_LIMIT"
    }


@pytest.mark.parametrize("path", ["chat", "chat/stream"])
async def test_auto_one_request_is_refused_when_its_hold_alone_exceeds_the_budget(
    http, world, path
):
    # $1000/Mtok output * 800 = $0.80; a $0.50 budget can never admit even the first request.
    configure(**AUTO, **EXPENSIVE, ai_daily_budget_usd="0.50")
    calls = []
    openrouter(lambda r: calls.append(r) or httpx.Response(200, json=auto_body({"cost": 0.0001})))
    auth = await headers(http)
    response = await chat(http, auth, path=path)
    assert response.status_code == 429 and "AI_BUDGET_LIMIT" in response.text
    assert calls == [] and await rows(world) == []


async def test_auto_interrupted_stream_without_usage_keeps_the_whole_hold(http, world):
    settings = configure(**AUTO)
    await headers(http)

    class Provider(FakeProvider):
        async def stream(self, messages):
            yield Completion("partial", "openrouter/auto")
            yield Completion(" more", "openrouter/auto")

    async with world.session() as db:
        user = await db.scalar(select(User).options(selectinload(User.profile)))
        response = await stream_chat(
            payload=ChatRequest(message="Hi"),
            request=Disconnecting(after=1),
            user=user,
            db=db,
            settings=settings,
            provider=Provider(),
        )
        [chunk async for chunk in response.body_iterator]
    (row,) = await rows(world)
    assert row.status == "failed" and row.cost_source == "reserved"
    assert row.cost_microusd == row.reserved_microusd > 0
