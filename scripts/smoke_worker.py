"""Check the local Cloudflare Worker runtime without Telegram or model calls."""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import tempfile
import time
from contextlib import suppress
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
STARTUP_TIMEOUT_SECONDS = 180


def available_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def status(url: str, *, method: str = "GET", body: bytes | None = None) -> int:
    request = Request(url, data=body, method=method)
    try:
        with urlopen(request, timeout=2) as response:
            return response.status
    except HTTPError as error:
        return error.code


def wait_for_worker(process: subprocess.Popen[bytes], base_url: str) -> None:
    deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Worker exited during startup ({process.returncode})")
        try:
            if status(f"{base_url}/smoke-secret") == 405:
                return
        except (TimeoutError, URLError):
            pass
        time.sleep(0.5)
    raise TimeoutError("Worker did not become ready within 180 seconds")


def check(
    base_url: str,
    path: str,
    expected: int,
    *,
    method: str = "GET",
    body: bytes | None = None,
) -> None:
    actual = status(f"{base_url}{path}", method=method, body=body)
    if actual != expected:
        raise AssertionError(f"{path}: expected HTTP {expected}, got {actual}")
    print(f"PASS {path}: HTTP {actual}")


def stop_worker(process: subprocess.Popen[bytes]) -> None:
    with suppress(ProcessLookupError):
        os.killpg(process.pid, signal.SIGTERM)

    with suppress(subprocess.TimeoutExpired):
        process.wait(timeout=2)

    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            os.killpg(process.pid, 0)
        except ProcessLookupError:
            break
        time.sleep(0.1)
    else:
        with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)

    if process.poll() is None:
        process.kill()
        process.wait()


def main() -> None:
    port = available_port()
    base_url = f"http://127.0.0.1:{port}"
    command = [
        "uv",
        "run",
        "pywrangler",
        "dev",
        "--local",
        "--ip",
        "127.0.0.1",
        "--port",
        str(port),
        "--var",
        "TELEGRAM_BOT_TOKEN:smoke-token",
        "--var",
        "WEBHOOK_SECRET_PATH:smoke-secret",
        "--var",
        "OPENAI_API_KEY:smoke-key",
        "--var",
        "LLM_PROVIDER:chatgpt",
        "--show-interactive-dev-session=false",
    ]
    with tempfile.TemporaryFile() as log:
        process = subprocess.Popen(
            command, cwd=ROOT, stdout=log, stderr=log, start_new_session=True
        )
        try:
            wait_for_worker(process, base_url)
            check(base_url, "/wrong-path", 404)
            check(base_url, "/smoke-secret", 405)
            check(base_url, "/smoke-secret", 400, method="POST", body=b"{")
            check(
                base_url,
                "/smoke-secret",
                400,
                method="POST",
                body=json.dumps([]).encode(),
            )
            check(
                base_url,
                "/smoke-secret",
                200,
                method="POST",
                body=json.dumps({"message": {}}).encode(),
            )
        except Exception:
            log.seek(0)
            print(log.read().decode(errors="replace")[-4000:])
            raise
        finally:
            stop_worker(process)

    print("Worker runtime smoke test passed; no Telegram or model calls were made.")


if __name__ == "__main__":
    main()
