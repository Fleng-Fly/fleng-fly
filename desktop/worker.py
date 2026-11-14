"""Local-only FastAPI worker. Its parent owns the stdin lifetime pipe."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import socket
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


def main() -> None:
    directory = Path(os.environ["FLENG_DESKTOP_DATA"])
    ready = Path(os.environ["FLENG_DESKTOP_READY"])
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(128)
    port = listener.getsockname()[1]
    os.environ.update(
        APP_ENV="development",
        DATABASE_URL="sqlite+aiosqlite:///" + (directory / "fleng.db").as_posix(),
        JWT_ACCESS_SECRET=(directory / "jwt-secret.txt").read_text(encoding="utf-8").strip(),
        FRONTEND_DIR=str(ROOT / "frontend"),
        PORT=str(port),
        CORS_ORIGIN=f"http://127.0.0.1:{port}",
        RENDER_EXTERNAL_URL="",
        TRUSTED_PROXY_IPS="",
        COOKIE_SECURE="false",
        COOKIE_SAMESITE="lax",
        REFRESH_COOKIE_NAME="fleng_desktop_refresh",
    )
    import uvicorn
    from app.db.prepare import main as prepare_database
    from starlette.middleware.trustedhost import TrustedHostMiddleware

    prepare_database()
    from app.main import create_app

    app = create_app()
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1"])
    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host="127.0.0.1",
            port=port,
            proxy_headers=False,
            workers=1,
            access_log=False,
            timeout_graceful_shutdown=5,
        )
    )
    parent_gone = threading.Event()

    def watch_parent() -> None:
        try:
            sys.stdin.buffer.read()  # closed automatically even if the GUI crashes
        finally:
            parent_gone.set()

    threading.Thread(target=watch_parent, daemon=True).start()

    async def supervise() -> None:
        task = asyncio.create_task(server.serve(sockets=[listener]))
        try:
            while not task.done():
                if parent_gone.is_set():
                    server.should_exit = True
                if server.started and not ready.exists() and not server.should_exit:
                    temporary = ready.with_suffix(".tmp")
                    temporary.write_text(
                        json.dumps({"port": port, "token": os.environ["FLENG_DESKTOP_TOKEN"]}),
                        encoding="utf-8",
                    )
                    temporary.replace(ready)
                await asyncio.sleep(0.05)
            await task
        finally:
            server.should_exit = True
            ready.unlink(missing_ok=True)
            listener.close()

    asyncio.run(supervise())


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Avoid logging exception strings that could contain SQL parameters.
        logging.error("Desktop backend failed (%s)", type(exc).__name__)
        raise SystemExit(1) from None
