from pathlib import Path

from src import desktop
from src.weebarr import runtime


def test_desktop_launcher_environment_uses_local_server_defaults(monkeypatch):
    monkeypatch.setenv("HOME", "/tmp/example-home")

    env = desktop.launcher_environment("127.0.0.1", 18080)

    assert env["WEEBARR_DESKTOP_MODE"] == "1"
    assert env["WEEBARR_HOST"] == "127.0.0.1"
    assert env["WEEBARR_PORT"] == "18080"
    assert env["WEEBARR_PUBLIC_URL"] == "http://127.0.0.1:18080"
    assert env["WEEBARR_PLEX_CLIENT_ID"] == "weebarr-desktop"
    assert env["WEEBARR_CONFIG_PATH"].endswith("Weebarr/config/weebarr.json")


def test_build_server_command_uses_module_in_dev_mode(monkeypatch):
    monkeypatch.setattr(desktop.sys, "frozen", False, raising=False)
    monkeypatch.setattr(desktop.sys, "executable", "/usr/bin/python3")

    command = desktop.build_server_command("127.0.0.1", 18080)

    assert command == [
        "/usr/bin/python3",
        "-m",
        "src.desktop",
        "--server",
        "--host",
        "127.0.0.1",
        "--port",
        "18080",
    ]


def test_desktop_app_dir_uses_platform_specific_base():
    windows_dir = runtime.desktop_app_dir(
        {"LOCALAPPDATA": r"C:\Users\Deep\AppData\Local"},
        os_name="nt",
        platform_name="win32",
        home=Path(r"C:\Users\Deep"),
    )
    mac_dir = runtime.desktop_app_dir(
        {},
        os_name="posix",
        platform_name="darwin",
        home=Path("/Users/deep"),
    )
    linux_dir = runtime.desktop_app_dir(
        {"XDG_CONFIG_HOME": "/home/deep/.config"},
        os_name="posix",
        platform_name="linux",
        home=Path("/home/deep"),
    )

    assert windows_dir == Path(r"C:\Users\Deep\AppData\Local") / "Weebarr"
    assert mac_dir == Path("/Users/deep/Library/Application Support/Weebarr")
    assert linux_dir == Path("/home/deep/.config/Weebarr")


def test_desktop_mode_enabled_when_requested():
    assert runtime.desktop_mode_enabled({"WEEBARR_DESKTOP_MODE": "true"}, frozen=False)
    assert not runtime.desktop_mode_enabled({}, frozen=False)
