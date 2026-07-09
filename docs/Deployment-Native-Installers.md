---
title: Native Desktop Installers
---

# Native Desktop Installers

Weebarr can now be installed like a local desktop app instead of only running in Docker.

This path is meant for people who want Sonarr-style behavior:

- install Weebarr with a normal platform installer
- launch it from the OS app list or desktop shortcut
- let it start a local background Weebarr server
- open the browser to the local web UI automatically

Under the hood, it is still the same Weebarr web app. The installer wraps that app in a local launcher instead of a container.

## Downloads

Native desktop builds are published on GitHub Releases:

- [Weebarr Releases](https://github.com/DeepDaddyTTV/weebarr/releases)

Typical release assets:

- `Windows`: `Weebarr-<version>-Windows-x64-Setup.exe`
- `macOS`: `Weebarr-<version>-macOS.dmg`
- `Linux`: `Weebarr-<version>-Linux-amd64.deb`
- `Linux`: `Weebarr-<version>-Linux-x86_64.rpm`
- `Linux`: `Weebarr-<version>-Linux-amd64.tar.gz`

## How It Behaves

When you launch the native app:

1. Weebarr starts a local server bound to `127.0.0.1`.
2. It prefers local desktop storage for config and logs.
3. It opens the seasonal dashboard in your default browser.
4. The background server stays running so future launches reopen the same local app quickly.

This is different from the mobile PWA path. The PWA uses your existing hosted URL. The native desktop build starts a local Weebarr instance on the machine where it is installed.

## Default Local Storage

The native desktop build keeps its own local config instead of using Docker's `/config` mount.

- `Windows`: `%LOCALAPPDATA%\\Weebarr\\config\\weebarr.json`
- `macOS`: `~/Library/Application Support/Weebarr/config/weebarr.json`
- `Linux`: `~/.config/Weebarr/config/weebarr.json`

Launcher logs live alongside that desktop app data:

- `Windows`: `%LOCALAPPDATA%\\Weebarr\\logs\\`
- `macOS`: `~/Library/Application Support/Weebarr/logs/`
- `Linux`: `~/.config/Weebarr/logs/`

## Windows

Use the `.exe` installer.

1. Download `Weebarr-<version>-Windows-x64-Setup.exe`.
2. Run it normally.
3. Launch **Weebarr** from the Start Menu or desktop shortcut.
4. Your browser should open to the local Weebarr UI.

The installer also includes a **Stop Weebarr** shortcut so you can stop the background local server without opening Task Manager.

## macOS

Use the `.dmg` release.

1. Download `Weebarr-<version>-macOS.dmg`.
2. Open the disk image.
3. Drag **Weebarr.app** into `Applications`.
4. Launch **Weebarr** from Launchpad or Finder.

The app opens the browser to the local dashboard and keeps the local server running in the background after launch.

If macOS warns you because the build came from GitHub instead of the App Store, use the normal right-click then **Open** flow the first time.

## Linux

Linux releases come in a few forms so you can pick what matches your distro.

### Debian and Ubuntu

Use the `.deb` package:

```bash
sudo dpkg -i Weebarr-<version>-Linux-amd64.deb
```

Then launch **Weebarr** from your applications menu.

### Fedora, RHEL, and compatible RPM distros

Use the `.rpm` package:

```bash
sudo rpm -i Weebarr-<version>-Linux-x86_64.rpm
```

Then launch **Weebarr** from your applications menu.

### Portable Linux Build

If you do not want to install a system package, extract the tarball:

```bash
tar -xzf Weebarr-<version>-Linux-amd64.tar.gz
cd Weebarr
./Weebarr
```

## First Launch and Setup

The native app still uses the same Weebarr setup flow:

1. Configure auth first.
2. Continue into request-backend setup.
3. Choose `Seerr` or `Sonarr Direct`.

If you choose `Sonarr Direct`, Weebarr still validates the Sonarr API key and loads the live dropdown options for root folder and quality profile just like the Docker build.

## Updating a Native Install

Native installs are updated differently from containers.

- `Windows`: run the newer `.exe` installer over the existing install
- `macOS`: replace the app with the newer `.dmg` release
- `Linux`: install the newer `.deb` or `.rpm`, or replace the extracted tarball folder

Your local desktop config should remain intact as long as you keep the same user profile on that machine.

If you are using Docker instead, keep using the [Update Container](Update-Container.md) guide instead of this page.

## Native Desktop vs PWA

Use **Native Desktop Installers** when:

- you want a local background Weebarr service on your computer
- you want normal OS installers and app shortcuts
- you do not want Docker for that machine

Use **Install as an App** when:

- you already host Weebarr somewhere else
- you just want a phone or tablet home-screen shortcut
- you want the browser-powered mobile shell, not a local install
