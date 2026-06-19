---
title: Home
---

# Weebarr Wiki

Welcome to the Weebarr wiki.

Weebarr is a seasonal anime dashboard for people who run their own media setup. It helps you see what is airing, check what you already have or requested, and send new anime requests through either Seerr or Sonarr Direct without bouncing between a bunch of different tabs.

You do not need to understand every setting before using it. Start with the deployment guide for your system, complete the two-stage setup, choose your request backend after auth, then use the Seasonal page as your main dashboard.

## Interface Preview

![Weebarr dark mode dashboard](assets/img/dark-mode.jpeg)

![Weebarr light mode dashboard](assets/img/light-mode.jpeg)

## What Weebarr Does

Weebarr brings together:

- seasonal anime information from AniList
- request and availability status from the active request backend
- one-click Seerr requests or Sonarr Direct request modals
- a simple login system
- optional Plex auth login
- themes
- optional automation for requesting seasonal anime by bucket

In plain English: Weebarr helps you answer, “What anime is airing, do I already have it, and should I request it?”

## Downloads and Links

- [GitHub Repository](https://github.com/DeepDaddyTTV/weebarr)
- [GitHub Pages Docs](https://deepdaddyttv.github.io/weebarr/)
- [Docker Hub Image](https://hub.docker.com/repository/docker/deepdaddyttv/weebarr/general)

## Pages in This Wiki

- [Features](Features.md)  
  Learn what each main page in Weebarr does.

- [Settings](Settings.md)  
  Understand the Settings page without needing to guess what each toggle means.

- [Theme Template](Theme-Template.md)  
  Use the reference theme manifest and sample JSON to build your own themes.

- [Docker Desktop on Windows](Deployment-Docker-Desktop-Windows.md)  
  Recommended if you are running Weebarr on a Windows machine with Docker Desktop.

- [Docker Desktop on Linux](Deployment-Docker-Desktop-Linux.md)  
  Recommended if you are running Docker Desktop on Linux.

- [Docker Hub](Deployment-Docker-Hub.md)  
  Use the published Docker Hub image directly if that is your preferred registry.

- [Other Deployment Options](Deployment-Other-Options.md)  
  For Docker Engine, Portainer, reverse proxies, Cloudflare Tunnel, custom images, and development use.

- [Troubleshooting](Troubleshooting.md)  
  Start here when something does not connect, request, import, or display correctly.

- [API Reference](API-Reference.md)  
  For users who want to connect health checks, automation, or external tools.

## Recommended Setup Path

If this is your first time setting up Weebarr, use this order:

1. Pick one deployment guide:
   - [Docker Desktop on Windows](Deployment-Docker-Desktop-Windows.md)
   - [Docker Desktop on Linux](Deployment-Docker-Desktop-Linux.md)
   - [Docker Hub](Deployment-Docker-Hub.md)
   - [Other Deployment Options](Deployment-Other-Options.md)
2. Start Weebarr and complete the first-run access setup.
3. Continue to the request-backend setup step after auth is configured.
4. Choose `Seerr` or `Sonarr Direct`.
5. If you choose `Sonarr Direct`, choose `http` or `https`, enter the Sonarr host and port (default `8989`), then validate the API key so Weebarr can load the live folder and profile dropdowns before you save the backend settings. You can still use `Skip Setup` if you want to finish backend config later in **Settings**.
6. Use the test action if needed, then open the **Seasonal** page.
7. Request titles manually, or enable automation later after you understand the buckets.

## Main Ideas

### Seasonal

The Seasonal page is the main screen. It shows current or selected seasonal anime and groups them into buckets such as `S-Tier`, `Canon`, `Bingeable`, and `Filler`.

### Requests

The Requests page only shows requests made through Weebarr. It is not meant to replace your full Seerr request history or your full Sonarr library history.

### Availability

Weebarr checks the active request backend and tries to show whether a title is already available, already requested or tracked, partly available, missing, or not matched.

### Automation

Automation can request shows for you based on the buckets you choose. It intentionally skips titles that are already requested or already available.

### Settings

Settings control themes, content filtering, automation, login options, API-key access, and how Weebarr talks to the active request backend.

![Weebarr settings overview](assets/img/settings-weebarr.jpeg)

## Before You Start

You should already have:

- Docker or Docker Desktop
- a working Seerr instance if you plan to use Seerr
- a working Sonarr instance if you plan to use Sonarr Direct
- an API key for the backend you plan to use first
- a folder where Weebarr can save its config

Your config folder matters. Keep it mounted and backed up. That is where Weebarr stores its settings, request history, theme imports, automation history, API key state, and login setup.
