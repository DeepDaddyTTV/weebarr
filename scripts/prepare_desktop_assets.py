#!/usr/bin/env python3
"""Generate platform icons for native Weebarr desktop installers."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ICON = (
    ROOT
    / "docs"
    / "Weebarr_Icon_PWA Exports"
    / "Weebarr_Icon_PWA-iOS-Dark-1024x1024@1x.png"
)
OUTPUT_DIR = ROOT / "packaging" / "desktop" / "generated"


def _resize_icon(source: Image.Image, size: int) -> Image.Image:
    return source.resize((size, size), Image.Resampling.LANCZOS)


def build_windows_icon(source: Image.Image) -> Path:
    output_path = OUTPUT_DIR / "weebarr-windows.ico"
    ico_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    source.save(output_path, format="ICO", sizes=ico_sizes)
    return output_path


def build_linux_icon(source: Image.Image) -> Path:
    output_path = OUTPUT_DIR / "weebarr-linux.png"
    _resize_icon(source, 512).save(output_path, format="PNG")
    return output_path


def build_macos_icon(source: Image.Image) -> Path:
    iconset_dir = OUTPUT_DIR / "weebarr.iconset"
    if iconset_dir.exists():
        shutil.rmtree(iconset_dir)
    iconset_dir.mkdir(parents=True, exist_ok=True)

    icon_sizes = {
        "icon_16x16.png": 16,
        "icon_16x16@2x.png": 32,
        "icon_32x32.png": 32,
        "icon_32x32@2x.png": 64,
        "icon_128x128.png": 128,
        "icon_128x128@2x.png": 256,
        "icon_256x256.png": 256,
        "icon_256x256@2x.png": 512,
        "icon_512x512.png": 512,
        "icon_512x512@2x.png": 1024,
    }
    for filename, size in icon_sizes.items():
        _resize_icon(source, size).save(iconset_dir / filename, format="PNG")

    output_path = OUTPUT_DIR / "weebarr-macos.icns"
    subprocess.run(
        ["iconutil", "-c", "icns", str(iconset_dir), "-o", str(output_path)],
        check=True,
    )
    return output_path


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with Image.open(SOURCE_ICON) as raw_source:
        source = raw_source.convert("RGBA")
        windows_icon = build_windows_icon(source)
        linux_icon = build_linux_icon(source)
        print(windows_icon)
        print(linux_icon)
        if shutil.which("iconutil"):
            print(build_macos_icon(source))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
