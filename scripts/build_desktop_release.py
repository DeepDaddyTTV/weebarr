#!/usr/bin/env python3
"""Build native Weebarr desktop installers for one target platform."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD_ROOT = ROOT / "build" / "desktop"
DIST_ROOT = BUILD_ROOT / "dist"
WORK_ROOT = BUILD_ROOT / "work"
SPEC_ROOT = BUILD_ROOT / "spec"
ARTIFACT_ROOT = ROOT / "dist-native"
GENERATED_ROOT = ROOT / "packaging" / "desktop" / "generated"


def app_version() -> str:
    match = re.search(
        r'^version\s*=\s*"([^"]+)"',
        (ROOT / "pyproject.toml").read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    if not match:
        raise RuntimeError("Could not determine version from pyproject.toml")
    return match.group(1)


def run(command: list[str], *, cwd: Path | None = None) -> None:
    subprocess.run(command, cwd=cwd or ROOT, check=True)


def clean_build_dirs() -> None:
    for path in (DIST_ROOT, WORK_ROOT, SPEC_ROOT, ARTIFACT_ROOT):
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)


def prepare_assets() -> None:
    run([sys.executable, str(ROOT / "scripts" / "prepare_desktop_assets.py")])


def pyinstaller_data_arg() -> str:
    separator = ";" if sys.platform.startswith("win") else ":"
    return f"{ROOT / 'src' / 'web'}{separator}src/web"


def build_pyinstaller(target_platform: str) -> Path:
    icon_path = GENERATED_ROOT / (
        "weebarr-windows.ico"
        if target_platform == "windows"
        else "weebarr-macos.icns" if target_platform == "macos" else "weebarr-linux.png"
    )
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--windowed",
        "--name",
        "Weebarr",
        "--paths",
        str(ROOT),
        "--distpath",
        str(DIST_ROOT),
        "--workpath",
        str(WORK_ROOT),
        "--specpath",
        str(SPEC_ROOT),
        "--icon",
        str(icon_path),
        "--add-data",
        pyinstaller_data_arg(),
        str(ROOT / "src" / "desktop.py"),
    ]
    if target_platform == "macos":
        command.extend(["--osx-bundle-identifier", "io.github.deepdaddyttv.weebarr"])
    run(command)
    app_dir = DIST_ROOT / ("Weebarr.app" if target_platform == "macos" else "Weebarr")
    if not app_dir.exists():
        raise RuntimeError(f"PyInstaller output missing: {app_dir}")
    return app_dir


def build_windows_installer(app_dir: Path, version: str) -> list[Path]:
    output_filename = f"Weebarr-{version}-Windows-x64-Setup.exe"
    run(
        [
            "iscc",
            f"/DAppVersion={version}",
            f"/DSourceDir={app_dir}",
            f"/DOutputDir={ARTIFACT_ROOT}",
            str(ROOT / "packaging" / "desktop" / "windows" / "Weebarr.iss"),
        ]
    )
    return [ARTIFACT_ROOT / output_filename]


def build_macos_dmg(app_dir: Path, version: str) -> list[Path]:
    output_path = ARTIFACT_ROOT / f"Weebarr-{version}-macOS.dmg"
    run(
        [
            "hdiutil",
            "create",
            "-volname",
            "Weebarr",
            "-srcfolder",
            str(app_dir),
            "-ov",
            "-format",
            "UDZO",
            str(output_path),
        ]
    )
    return [output_path]


def _write_linux_desktop_file(destination: Path) -> None:
    template = (ROOT / "packaging" / "desktop" / "linux" / "weebarr.desktop").read_text(
        encoding="utf-8"
    )
    destination.write_text(
        template.replace("@INSTALL_PATH@", "/opt/weebarr/Weebarr"),
        encoding="utf-8",
    )


def _collect_new_artifact(extension: str, before: set[Path]) -> Path:
    current = set(ARTIFACT_ROOT.glob(f"*{extension}"))
    new_paths = sorted(current - before)
    if not new_paths:
        raise RuntimeError(f"No new {extension} artifact was produced")
    return new_paths[-1]


def build_linux_packages(app_dir: Path, version: str) -> list[Path]:
    stage_root = BUILD_ROOT / "linux-stage"
    if stage_root.exists():
        shutil.rmtree(stage_root)
    (stage_root / "opt" / "weebarr").mkdir(parents=True, exist_ok=True)
    shutil.copytree(app_dir, stage_root / "opt" / "weebarr", dirs_exist_ok=True)

    desktop_dir = stage_root / "usr" / "share" / "applications"
    desktop_dir.mkdir(parents=True, exist_ok=True)
    _write_linux_desktop_file(desktop_dir / "weebarr.desktop")

    icon_dir = stage_root / "usr" / "share" / "icons" / "hicolor" / "512x512" / "apps"
    icon_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(GENERATED_ROOT / "weebarr-linux.png", icon_dir / "weebarr.png")

    common_args = [
        "fpm",
        "-s",
        "dir",
        "-n",
        "weebarr",
        "-v",
        version,
        "-a",
        "amd64",
        "--license",
        "GPL-3.0",
        "--maintainer",
        "DeepDaddyTTV",
        "--vendor",
        "DeepDaddyTTV",
        "--url",
        "https://github.com/DeepDaddyTTV/weebarr",
        "--description",
        "Seasonal anime discovery and request dashboard for Seerr or Sonarr Direct",
        "-C",
        str(stage_root),
        "opt",
        "usr",
    ]

    before_deb = set(ARTIFACT_ROOT.glob("*.deb"))
    run(common_args[:1] + ["-t", "deb"] + common_args[1:], cwd=ARTIFACT_ROOT)
    deb_path = _collect_new_artifact(".deb", before_deb)
    deb_target = ARTIFACT_ROOT / f"Weebarr-{version}-Linux-amd64.deb"
    deb_path.replace(deb_target)

    before_rpm = set(ARTIFACT_ROOT.glob("*.rpm"))
    run(common_args[:1] + ["-t", "rpm"] + common_args[1:], cwd=ARTIFACT_ROOT)
    rpm_path = _collect_new_artifact(".rpm", before_rpm)
    rpm_target = ARTIFACT_ROOT / f"Weebarr-{version}-Linux-x86_64.rpm"
    rpm_path.replace(rpm_target)

    tarball_path = ARTIFACT_ROOT / f"Weebarr-{version}-Linux-amd64.tar.gz"
    with tarfile.open(tarball_path, "w:gz") as archive:
        archive.add(app_dir, arcname="Weebarr")

    return [deb_target, rpm_target, tarball_path]


def build_artifacts(target_platform: str) -> list[Path]:
    version = app_version()
    clean_build_dirs()
    prepare_assets()
    app_dir = build_pyinstaller(target_platform)
    if target_platform == "windows":
        return build_windows_installer(app_dir, version)
    if target_platform == "macos":
        return build_macos_dmg(app_dir, version)
    if target_platform == "linux":
        return build_linux_packages(app_dir, version)
    raise ValueError(f"Unsupported platform: {target_platform}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build native Weebarr installers")
    parser.add_argument(
        "--platform",
        choices=("linux", "macos", "windows"),
        required=True,
        help="Target platform to package",
    )
    args = parser.parse_args()
    artifacts = build_artifacts(args.platform)
    for artifact in artifacts:
        print(artifact)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
