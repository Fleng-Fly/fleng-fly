"""A real desktop window; closing it stops its own local server."""

from __future__ import annotations

import html
import logging
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from desktop.runtime import (  # noqa: E402
    AlreadyRunning,
    DesktopServer,
    InstanceLock,
    StartupCancelled,
    default_data_dir,
)

logger = logging.getLogger("fleng.desktop")


def configure_logging(directory: Path) -> Path:
    """pythonw has no console streams; provide real UTF-8 file streams."""
    path = directory / "desktop.log"
    if path.exists() and path.stat().st_size > 2_000_000:
        path.replace(directory / "desktop.previous.log")
    stream = path.open("a", encoding="utf-8", buffering=1)
    if sys.stdout is None:
        sys.stdout = stream
    if sys.stderr is None:
        sys.stderr = stream
    logging.basicConfig(stream=stream, level=logging.INFO, force=True)
    logger.info("Starting Fleng: Python %s, platform %s", sys.version, sys.platform)
    return path


STYLE = """body{margin:0;background:#101126;color:#f5f3ff;font:18px/1.6 system-ui;
min-height:100vh;display:grid;place-items:center}main{max-width:650px;padding:32px}
h1{font-size:40px;line-height:1.1}p{color:#c7c0df}.brand{color:#b59aff;letter-spacing:4px}
.pulse{width:40px;height:40px;border-radius:50%;border:4px solid #352553;
border-top-color:#ad91ff;animation:spin 1s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}"""


def page(title: str, message: str, loading: bool = False) -> str:
    return (
        '<!doctype html><html lang="uk"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<style>{STYLE}</style><main><p class=brand>FLENG</p><h1>{html.escape(title)}</h1>"
        f"<p>{html.escape(message)}</p>"
        + ('<div class="pulse"></div>' if loading else "")
        + "</main></html>"
    )


def show_message(message: str) -> None:
    if sys.platform == "win32":
        import ctypes

        ctypes.windll.user32.MessageBoxW(None, message, "Fleng", 0x40)
    else:
        print(message, file=sys.stderr)


def main() -> int:
    directory = default_data_dir()
    try:
        lock = InstanceLock(directory)
    except AlreadyRunning as exc:
        show_message(str(exc))
        return 0
    except OSError:
        show_message("Fleng не може відкрити папку локальних даних. Перевір права доступу.")
        return 1
    server = DesktopServer(ROOT, directory)
    closed = threading.Event()
    try:
        configure_logging(directory)
        if sys.platform == "win32":
            from desktop.chromium import run_browser_window

            origin = server.start()
            run_browser_window(origin + "/dashboard.html", directory)
            return 0
        import webview

        window = webview.create_window(
            "Fleng — English",
            html=page("Готуємо твоє навчання", "Запускаємо Fleng. Це займе кілька секунд.", True),
            width=1180,
            height=820,
            min_size=(760, 580),
            background_color="#101126",
        )
        window.events.closed += closed.set

        def launch() -> None:
            try:
                origin = server.start()
                if not closed.is_set():
                    window.load_url(origin + "/dashboard.html")
            except StartupCancelled:
                pass
            except Exception:
                logger.exception("Desktop backend startup failed")
                server.stop()
                if not closed.is_set():
                    window.load_html(
                        page(
                            "Не вдалося запустити Fleng",
                            f"Перевір журнал {directory / 'backend.log'}",
                        )
                    )

        # No Python bridge is exposed to page JavaScript. Profile lives with user
        # data, outside the archive, so cookies survive application updates.
        webview.start(
            launch,
            gui="qt",
            private_mode=False,
            storage_path=str(directory / "webview"),
            debug=False,
        )
        return 0
    except Exception as exc:
        logger.exception("Desktop startup failed")
        show_message(
            f"Не вдалося відкрити Fleng: {type(exc).__name__}: {str(exc)[:250]}\n\n"
            f"Точна помилка: {directory / 'desktop.log'}\n"
            f"Журнал сервера: {directory / 'backend.log'}"
        )
        return 1
    finally:
        closed.set()
        server.stop()
        lock.close()


if __name__ == "__main__":
    raise SystemExit(main())
