# Native Desktop Installers

Weebarr can now be installed like a local desktop app instead of only running in Docker.

This path is meant for Sonarr-style behavior:

- install Weebarr with a normal platform installer
- launch it from the OS app list or desktop shortcut
- let it start a local background Weebarr server
- open the browser to the local UI automatically

Native downloads are published on GitHub Releases:

- [Weebarr Releases](https://github.com/DeepDaddyTTV/weebarr/releases)

Typical assets:

- `Windows`: `Weebarr-<version>-Windows-x64-Setup.exe`
- `macOS`: `Weebarr-<version>-macOS.dmg`
- `Linux`: `Weebarr-<version>-Linux-amd64.deb`
- `Linux`: `Weebarr-<version>-Linux-x86_64.rpm`
- `Linux`: `Weebarr-<version>-Linux-amd64.tar.gz`

## Default Storage

The native build stores config locally instead of using Docker's `/config` mount.

- `Windows`: `%LOCALAPPDATA%\\Weebarr\\config\\weebarr.json`
- `macOS`: `~/Library/Application Support/Weebarr/config/weebarr.json`
- `Linux`: `~/.config/Weebarr/config/weebarr.json`

## Windows

1. Download `Weebarr-<version>-Windows-x64-Setup.exe`.
2. Run it normally.
3. Launch **Weebarr** from the Start Menu or desktop shortcut.

The installer also includes a **Stop Weebarr** shortcut for the background local server.

## macOS

1. Download `Weebarr-<version>-macOS.dmg`.
2. Open it.
3. Drag **Weebarr.app** into `Applications`.
4. Launch **Weebarr**.

## Linux

Pick the package type that fits your distro:

- `.deb` for Debian and Ubuntu
- `.rpm` for Fedora, RHEL, and compatible RPM distros
- `.tar.gz` for a portable unpack-and-run build

## Setup Flow

The app still uses the same two-stage setup:

1. auth first
2. request-backend selection after auth

If you choose `Sonarr Direct`, the native build still validates the API key and loads the live Sonarr dropdown choices the same way as the Docker build.

## Updating

Native installs are updated by installing the newer desktop release.

- `Windows`: rerun the newer `.exe`
- `macOS`: replace the app from the newer `.dmg`
- `Linux`: install the newer `.deb` or `.rpm`, or replace the extracted tarball folder

If you are using Docker instead, use [Update Container](Update-Container.md) rather than this page.
