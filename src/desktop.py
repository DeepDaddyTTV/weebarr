"""Desktop launcher for native Weebarr installs."""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import signal
import subprocess
import sys
import webbrowser
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import sleep
from typing import Any

import httpx
import uvicorn

from src.version import __version__
from src.weebarr.runtime import (
    desktop_config_path,
    desktop_log_dir,
    desktop_state_path,
)

APP_HOST = "127.0.0.1"
DEFAULT_PORT = 18080
MAX_PORT_SEARCH = 12
HEALTH_PATH = "/api/health"
DEFAULT_OPEN_PATH = "/seasonal"
SERVER_READY_TIMEOUT_SECONDS = 30.0
SERVER_READY_POLL_SECONDS = 0.5


@dataclass
class DesktopState:
    """Persisted launcher state for the local desktop server."""

    host: str
    port: int
    pid: int | None = None
    launched_at: str | None = None
    version: str | None = None

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


def _desktop_port() -> int:
    return int(os.getenv("WEEBARR_DESKTOP_PORT", str(DEFAULT_PORT)))


def health_url(host: str, port: int) -> str:
    return f"http://{host}:{port}{HEALTH_PATH}"


def app_url(host: str, port: int, path: str = DEFAULT_OPEN_PATH) -> str:
    return f"http://{host}:{port}{path}"


def launcher_environment(host: str, port: int) -> dict[str, str]:
    """Return the environment used for the background server."""

    config_path = desktop_config_path()
    return {
        **os.environ,
        "PYTHONUNBUFFERED": "1",
        "WEEBARR_DESKTOP_MODE": "1",
        "WEEBARR_HOST": host,
        "WEEBARR_PORT": str(port),
        "WEEBARR_PUBLIC_URL": f"http://{host}:{port}",
        "WEEBARR_CONFIG_PATH": str(config_path),
        "WEEBARR_PLEX_CLIENT_ID": "weebarr-desktop",
        "WEEBARR_PLEX_PRODUCT_NAME": "Weebarr Desktop",
        "WEEBARR_PLEX_PRODUCT_VERSION": __version__,
        "WEEBARR_PLEX_PLATFORM": sys.platform,
        "WEEBARR_VERSION_OVERRIDE": __version__,
    }


def load_state() -> DesktopState | None:
    path = desktop_state_path()
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return DesktopState(
            host=str(payload.get("host", APP_HOST)),
            port=int(payload.get("port", _desktop_port())),
            pid=int(payload["pid"]) if payload.get("pid") else None,
            launched_at=payload.get("launched_at"),
            version=payload.get("version"),
        )
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None


def save_state(state: DesktopState) -> None:
    path = desktop_state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(state)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def clear_state() -> None:
    path = desktop_state_path()
    with contextlib.suppress(FileNotFoundError):
        path.unlink()


def is_server_healthy(host: str, port: int, *, timeout: float = 1.5) -> bool:
    try:
        response = httpx.get(health_url(host, port), timeout=timeout)
        payload = response.json()
        return response.is_success and payload.get("app") == "weebarr"
    except Exception:
        return False


def choose_candidate_ports(preferred_port: int) -> list[int]:
    return list(range(preferred_port, preferred_port + MAX_PORT_SEARCH))


def build_server_command(host: str, port: int) -> list[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable, "--server", "--host", host, "--port", str(port)]
    return [
        sys.executable,
        "-m",
        "src.desktop",
        "--server",
        "--host",
        host,
        "--port",
        str(port),
    ]


def start_server(host: str, port: int) -> DesktopState:
    log_dir = desktop_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "weebarr-desktop.log"
    env = launcher_environment(host, port)
    log_handle = log_path.open("a", encoding="utf-8")
    cmd = build_server_command(host, port)

    popen_kwargs: dict[str, Any] = {
        "args": cmd,
        "cwd": Path.cwd(),
        "env": env,
        "stdout": log_handle,
        "stderr": subprocess.STDOUT,
        "close_fds": True,
    }
    if os.name == "nt":
        detached_process = int(getattr(subprocess, "DETACHED_PROCESS", 0))
        new_process_group = int(getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
        popen_kwargs["creationflags"] = detached_process | new_process_group
    else:
        popen_kwargs["start_new_session"] = True

    process = subprocess.Popen(**popen_kwargs)
    state = DesktopState(
        host=host,
        port=port,
        pid=process.pid,
        launched_at=datetime.now(timezone.utc).isoformat(),
        version=__version__,
    )
    save_state(state)
    return state


def wait_for_server(host: str, port: int, *, timeout_seconds: float) -> bool:
    waited = 0.0
    while waited < timeout_seconds:
        if is_server_healthy(host, port):
            return True
        sleep(SERVER_READY_POLL_SECONDS)
        waited += SERVER_READY_POLL_SECONDS
    return False


def open_browser(host: str, port: int) -> None:
    webbrowser.open(app_url(host, port), new=2)


def stop_running_server(state: DesktopState | None = None) -> bool:
    state = state or load_state()
    if state is None or state.pid is None:
        clear_state()
        return False

    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(state.pid), "/T", "/F"],
            check=False,
            capture_output=True,
        )
    else:
        with contextlib.suppress(ProcessLookupError):
            os.kill(state.pid, signal.SIGTERM)

    for _ in range(20):
        if not is_server_healthy(state.host, state.port):
            clear_state()
            return True
        sleep(0.25)

    return False


def launch(*, open_ui: bool = True, preferred_port: int | None = None) -> int:
    preferred_port = preferred_port or _desktop_port()
    state = load_state()
    if state and is_server_healthy(state.host, state.port):
        if open_ui:
            open_browser(state.host, state.port)
        return 0

    for port in choose_candidate_ports(preferred_port):
        if is_server_healthy(APP_HOST, port):
            reused = DesktopState(host=APP_HOST, port=port, version=__version__)
            save_state(reused)
            if open_ui:
                open_browser(APP_HOST, port)
            return 0

    for port in choose_candidate_ports(preferred_port):
        launched = start_server(APP_HOST, port)
        if wait_for_server(
            APP_HOST, port, timeout_seconds=SERVER_READY_TIMEOUT_SECONDS
        ):
            if open_ui:
                open_browser(APP_HOST, port)
            return 0
        stop_running_server(launched)

    return 1


def run_server(host: str, port: int) -> int:
    os.environ.update(launcher_environment(host, port))
    from src.main import create_app

    app = create_app()
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=os.getenv("WEEBARR_LOG_LEVEL", "info").lower(),
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Launch the native Weebarr desktop app"
    )
    parser.add_argument(
        "--server", action="store_true", help="Run the local server only"
    )
    parser.add_argument(
        "--stop", action="store_true", help="Stop the background Weebarr server"
    )
    parser.add_argument(
        "--status", action="store_true", help="Print current desktop server status"
    )
    parser.add_argument(
        "--no-open", action="store_true", help="Do not open the browser after launch"
    )
    parser.add_argument("--host", default=APP_HOST, help="Desktop host bind address")
    parser.add_argument(
        "--port", type=int, default=_desktop_port(), help="Preferred desktop port"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.server:
        return run_server(args.host, args.port)
    if args.stop:
        return 0 if stop_running_server() else 1
    if args.status:
        state = load_state()
        if state is None:
            print("stopped")
            return 1
        print(json.dumps(asdict(state), indent=2))
        return 0 if is_server_healthy(state.host, state.port) else 1
    return launch(open_ui=not args.no_open, preferred_port=args.port)


if __name__ == "__main__":
    raise SystemExit(main())
