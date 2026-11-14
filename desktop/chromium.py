"""Own an app-mode Chromium window using a dedicated Fleng browser profile.

The profile's loopback DevTools endpoint is used only to observe the window
lifetime; it never attaches to the user's normal browser profile.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import time
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import ProxyHandler, build_opener

logger = logging.getLogger("fleng.desktop")


def find_browser() -> Path:
    locations = []
    for name in ("PROGRAMFILES(X86)", "PROGRAMFILES", "LOCALAPPDATA"):
        if base := os.environ.get(name):
            locations.extend(
                [
                    Path(base) / "Microsoft/Edge/Application/msedge.exe",
                    Path(base) / "Google/Chrome/Application/chrome.exe",
                ]
            )
    for name in ("msedge.exe", "chrome.exe", "msedge", "google-chrome", "chromium"):
        if executable := shutil.which(name):
            locations.append(Path(executable))
    for path in locations:
        if path.is_file():
            return path
    raise RuntimeError("Для відкриття Fleng потрібен Microsoft Edge або Google Chrome.")


def read_debug_port(profile: Path) -> int | None:
    try:
        port = int((profile / "DevToolsActivePort").read_text().splitlines()[0])
        return port if 1 <= port <= 65535 else None
    except (OSError, ValueError, IndexError):
        return None


def wait_for_window(
    profile: Path,
    origin: str,
    process: subprocess.Popen,
    startup_timeout: float = 45,
    close_grace: float = 1.5,
) -> None:
    opener = build_opener(ProxyHandler({}))
    deadline = time.monotonic() + startup_timeout
    last_present = None
    expected = urlsplit(origin)
    while True:
        present = False
        port = read_debug_port(profile)
        if port:
            try:
                with opener.open(f"http://127.0.0.1:{port}/json/list", timeout=2) as response:
                    targets = json.load(response)
                present = any(
                    target.get("type") == "page"
                    and (url := urlsplit(target.get("url", ""))).scheme == expected.scheme
                    and url.netloc == expected.netloc
                    for target in targets
                )
            except (OSError, ValueError, TypeError):
                pass
        now = time.monotonic()
        if present:
            last_present = now
        elif last_present is not None and now - last_present >= close_grace:
            return
        elif last_present is None and now >= deadline:
            raise RuntimeError("Браузер не підтвердив відкриття вікна Fleng. Перевір desktop.log.")
        elif last_present is None and process.poll() not in (None, 0):
            raise RuntimeError("Edge або Chrome не зміг відкрити вікно Fleng.")
        time.sleep(0.25)


def run_browser_window(url: str, directory: Path) -> None:
    browser = find_browser()
    profile = directory / "browser-profile"
    profile.mkdir(parents=True, exist_ok=True)
    log = (directory / "browser.log").open("ab")
    process = None
    try:
        command = [
            str(browser),
            f"--app={url}",
            f"--user-data-dir={profile}",
            "--remote-debugging-port=0",
            "--remote-debugging-address=127.0.0.1",
            "--disable-background-mode",
            "--disable-extensions",
            "--no-first-run",
            "--no-default-browser-check",
            "--window-size=1180,820",
        ]
        logger.info("Starting browser app window: %s", browser.name)
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        parsed = urlsplit(url)
        wait_for_window(profile, f"{parsed.scheme}://{parsed.netloc}", process)
        logger.info("Fleng browser window closed")
    finally:
        # Terminate only the process started for our dedicated profile, never
        # kill browsers by name or touch the default Chrome/Edge profile.
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
        log.close()
