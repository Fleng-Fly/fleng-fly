"""Subprocess body for test_ai_sqlite_audit: one independent FastAPI-like worker process.

Usage (cwd=backend): _ai_race_worker.py DB START_EPOCH ATTEMPTS SETTLE USER_IDS
Prints the number of admitted reservations.
"""

import asyncio
import sys
import time
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.core.errors import ApiError
from app.db.models import User
from app.modules.ai import service
from app.modules.ai.provider import Completion


async def main(db: str, start: float, attempts: int, settle: bool, user_ids: list[str]) -> int:
    engine = create_async_engine(f"sqlite+aiosqlite:///{db}", connect_args={"timeout": 60})
    factory = async_sessionmaker(engine, expire_on_commit=False)
    settings = Settings(
        ai_enabled=True,
        openrouter_api_key="x",
        openrouter_model="test/model",
        ai_input_price_per_mtok_usd="0",
        ai_output_price_per_mtok_usd="500",  # 800 tokens = $0.40 reserved
        ai_requests_per_minute=100000,
        ai_concurrency=100,
        ai_daily_user_limit=5,
        ai_max_concurrent_requests=int(sys.argv[6]) if len(sys.argv) > 6 else 1,
    )
    admitted = 0
    await asyncio.sleep(max(0, start - time.time()))
    for index in range(attempts):
        async with factory() as session:
            user = await session.scalar(
                select(User).where(User.id == UUID(user_ids[index % len(user_ids)]))
            )
            try:
                usage = await service.reserve(
                    session, user, settings, [{"role": "user", "content": "hi"}]
                )
            except ApiError:
                continue
            admitted += 1
            if settle:
                await service.finish_usage(
                    session, usage, settings, Completion("ok", "test/model", {"cost": 0})
                )
    await engine.dispose()
    return admitted


if __name__ == "__main__":
    db, start, attempts, settle = (
        sys.argv[1],
        float(sys.argv[2]),
        int(sys.argv[3]),
        sys.argv[4] == "1",
    )
    print(asyncio.run(main(db, start, attempts, settle, sys.argv[5].split(","))))
