"""Own one local backend process and a persistent per-user data directory."""

from __future__ import annotations

import json
import os
import secrets
import sqlite3
import subprocess
import sys
import threading
import time
import uuid
from contextlib import closing
from pathlib import Path
from urllib.request import ProxyHandler, build_opener


class AlreadyRunning(RuntimeError):
    pass


class StartupCancelled(RuntimeError):
    pass


def default_data_dir() -> Path:
    if custom := os.environ.get("FLENG_DESKTOP_DATA"):
        return Path(custom).expanduser().resolve()
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    return base / "Fleng"


class InstanceLock:
    """OS-owned lock: a crashed application never leaves a stale running flag."""

    def __init__(self, directory: Path):
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.file = (directory / "desktop.lock").open("a+b")
        if self.file.seek(0, 2) == 0:
            self.file.write(b"0")
            self.file.flush()
        self.file.seek(0)
        try:
            if sys.platform == "win32":
                import msvcrt

                msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(self.file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.file.close()
            raise AlreadyRunning("Fleng уже відкрито. Перемкнись до його вікна.") from None

    def close(self) -> None:
        self.file.close()


def prepare_user_data(directory: Path, root: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    secret_path = directory / "jwt-secret.txt"
    try:
        descriptor = os.open(secret_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        pass
    else:
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            output.write(secrets.token_urlsafe(48))
    if len(secret_path.read_text(encoding="utf-8").strip()) < 32:
        raise RuntimeError(
            "Некоректний локальний ключ Fleng. Збережи дані та звернись по допомогу."
        )
    target = directory / "fleng.db"
    previous = root / "backend/data/fleng.db"
    if not target.exists() and previous.is_file():
        # SQLite's backup API includes committed WAL contents; never move/delete
        # the developer database and never overwrite an existing desktop database.
        temporary = directory / f"import-{uuid.uuid4().hex}.db"
        try:
            with (
                closing(
                    sqlite3.connect(previous.resolve().as_uri() + "?mode=ro", uri=True)
                ) as source,
                closing(sqlite3.connect(temporary)) as destination,
            ):
                source.backup(destination)
                destination.commit()
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)


class DesktopServer:
    def __init__(self, root: Path, directory: Path):
        self.root = root
        self.directory = directory
        self.token = secrets.token_urlsafe(24)
        self.ready_file = directory / f"ready-{uuid.uuid4().hex}.json"
        self.process: subprocess.Popen | None = None
        self.stopping = threading.Event()
        self._mutex = threading.Lock()
        self._log = None

    def start(self, timeout: float = 90) -> str:
        if self.stopping.is_set():
            raise StartupCancelled()
        prepare_user_data(self.directory, self.root)
        environment = {
            **os.environ,
            "FLENG_DESKTOP_DATA": str(self.directory),
            "FLENG_DESKTOP_READY": str(self.ready_file),
            "FLENG_DESKTOP_TOKEN": self.token,
            "PYTHONUNBUFFERED": "1",
        }
        executable = Path(sys.executable)
        if executable.name.lower() == "pythonw.exe":
            executable = executable.with_name("python.exe")
        log_path = self.directory / "backend.log"
        if log_path.exists() and log_path.stat().st_size > 5_000_000:
            log_path.replace(self.directory / "backend.previous.log")
        with self._mutex:
            if self.stopping.is_set():
                raise StartupCancelled()
            self._log = log_path.open("ab")
            try:
                self.process = subprocess.Popen(
                    [str(executable), str(self.root / "desktop/worker.py")],
                    cwd=self.root,
                    env=environment,
                    stdin=subprocess.PIPE,
                    stdout=self._log,
                    stderr=self._log,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                )
            except BaseException:
                self._log.close()
                raise
        opener = build_opener(ProxyHandler({}))  # loopback must never use a web proxy
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.stopping.is_set():
                raise StartupCancelled()
            if self.process.poll() is not None:
                raise RuntimeError("Сервер Fleng не запустився. Перевір backend.log у папці даних.")
            if self.ready_file.exists():
                info = json.loads(self.ready_file.read_text(encoding="utf-8"))
                if info.get("token") != self.token:
                    raise RuntimeError("Некоректна відповідь локального сервера.")
                port = info["port"]
                if not isinstance(port, int) or not 1 <= port <= 65535:
                    raise RuntimeError("Некоректний порт локального сервера.")
                origin = f"http://127.0.0.1:{port}"
                with opener.open(origin + "/api/v1/health/ready", timeout=3) as response:
                    if response.status == 200:
                        return origin
            self.stopping.wait(0.1)
        self.stop()
        raise RuntimeError("Запуск Fleng тривав надто довго. Перевір backend.log у папці даних.")

    def stop(self) -> None:
        self.stopping.set()
        with self._mutex:
            process = self.process
            if process is not None:
                if process.stdin is not None:
                    try:
                        process.stdin.close()  # EOF asks only our worker to shut down
                    except OSError:
                        pass
                try:
                    process.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    process.terminate()
                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=3)
                self.process = None
            if self._log is not None:
                self._log.close()
                self._log = None
            self.ready_file.unlink(missing_ok=True)
