---
title: Docker Desktop on Windows
---

# Deploying on Docker Desktop for Windows

This guide walks through running Weebarr on Windows using Docker Desktop.

Use this guide if your Docker setup is on a normal Windows machine and you want the simplest path to get Weebarr running.

## What You Need First

Before starting, make sure you have:

- Docker Desktop for Windows installed and running
- a working Seerr instance if you plan to use Seerr
- a working Sonarr instance if you plan to use Sonarr Direct
- an API key for the backend you plan to use first
- a folder where Weebarr can save its config

The config folder is important. It keeps your Weebarr settings safe when the container updates or restarts.

## Image Source

You can pull Weebarr from either published registry:

- `ghcr.io/deepdaddyttv/weebarr:latest`
- `deepdaddyttv/weebarr:latest`

This guide uses GHCR in the compose example, but swapping to Docker Hub is fine if you prefer it.

If you want to use Docker Desktop's UI instead of Compose first, you can also go to `Images`, pull `deepdaddyttv/weebarr:latest`, and create the container from there.

## Recommended Folder Layout

Create a folder like this:

```text
C:\Docker\Weebarr
├── compose.yml
└── config\
```

The `compose.yml` file is your Docker Compose file. The `config` folder is where Weebarr stores its settings.

## Example Compose File

Create `C:\Docker\Weebarr\compose.yml` and paste this in:

```yaml
services:
  weebarr:
    image: ghcr.io/deepdaddyttv/weebarr:latest
    container_name: weebarr
    environment:
      TZ: America/New_York
      WEEBARR_PUBLIC_URL: http://localhost:18080
      SEERR_BASE_URL: http://seerr:5055
      SEERR_API_KEY: change-me
      SEERR_REQUEST_SEASONS: all
    ports:
      - "18080:8888"
    volumes:
      - ./config:/config
    restart: unless-stopped
```

Change these values before starting:

- `TZ`: your timezone
- `SEERR_BASE_URL`: the URL Weebarr should use to reach Seerr
- `SEERR_API_KEY`: your Seerr API key

To use Docker Hub instead, change only the image line:

```yaml
image: deepdaddyttv/weebarr:latest
```

If you are just testing locally, you can leave `WEEBARR_PUBLIC_URL` as:

```text
http://localhost:18080
```

If you expose Weebarr through a domain later, update it to the public URL.

## Start Weebarr

Open PowerShell or Terminal in:

```text
C:\Docker\Weebarr
```

Run:

```powershell
docker compose up -d
```

Then open:

```text
http://localhost:18080
```

Complete the first-run setup. You can choose:

- local login
- Plex login
- both local and Plex login

Then continue to the request-backend step after auth, choose either `Seerr` or `Sonarr Direct`, and either save that backend or use `Skip Setup` if you want to finish it later in **Settings**.

If you choose `Sonarr Direct`, choose `http` or `https`, enter the Sonarr host and port (default `8989`), then validate the API key so Weebarr can load the live folder and profile dropdowns before you save.

## Important Windows Notes

### Keep the config folder mounted

Do not remove this line unless you know what you are doing:

```yaml
volumes:
  - ./config:/config
```

Without a persistent config folder, settings can disappear when the container is recreated.

### If Seerr is also in Docker

If Seerr is running in the same Docker network, use the Docker service name when possible:

```text
http://seerr:5055
```

That is usually better than using a Windows LAN IP.

### If Seerr is outside Docker

Use a URL that the Weebarr container can reach. A URL that works in your browser is not always the same as a URL that works from inside Docker.

If the connection test fails, start with the [Troubleshooting](Troubleshooting.md) page.

## Updating Weebarr

From the same folder as your compose file, run:

```powershell
docker compose pull
docker compose up -d
```

This pulls the newest image and recreates the container while keeping your mounted config folder.

## Backing Up Weebarr

Back up this folder:

```text
C:\Docker\Weebarr\config
```

That folder preserves:

- access settings
- request backend settings
- automation history
- theme imports
- API key state
- Weebarr request history

## Exposing Weebarr Publicly

If you expose Weebarr through a reverse proxy, HTTPS endpoint, or tunnel:

- set `WEEBARR_PUBLIC_URL` to the public URL
- use HTTPS
- keep rate limiting or access protection at the edge
- avoid exposing the raw container port directly if possible

Example public URL:

```text
https://weebarr.example.com
```
