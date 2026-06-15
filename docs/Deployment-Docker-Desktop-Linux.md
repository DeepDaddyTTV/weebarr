---
title: Docker Desktop on Linux
---

# Deploying on Docker Desktop for Linux

This guide walks through running Weebarr on Linux using Docker Desktop.

If you are using standard Docker Engine instead of Docker Desktop, see [Other Deployment Options](Deployment-Other-Options.md).

## What You Need First

Before starting, make sure you have:

- Docker Desktop for Linux installed and running
- a working Seerr instance if you plan to use Seerr
- a working Sonarr instance if you plan to use Sonarr Direct
- an API key for the backend you plan to use first
- a folder where Weebarr can save its config

The config folder is what keeps your settings, themes, auth setup, automation history, API key state, and request history between updates.

## Image Source

You can pull Weebarr from either published registry:

- `ghcr.io/deepdaddyttv/weebarr:latest`
- `deepdaddyttv/weebarr:latest`

This guide uses GHCR in the example, but Docker Hub works as a drop-in replacement.

If you want to use Docker Desktop's UI instead of Compose first, you can also go to `Images`, pull `deepdaddyttv/weebarr:latest`, and create the container from there.

## Recommended Folder Layout

Create a folder like this:

```text
~/docker/weebarr/
├── compose.yml
└── config/
```

## Example Compose File

Create `~/docker/weebarr/compose.yml` and paste this in:

```yaml
services:
  weebarr:
    image: ghcr.io/deepdaddyttv/weebarr:latest
    container_name: weebarr
    environment:
      TZ: UTC
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

If you want Docker Hub instead of GHCR, swap the image line to:

```yaml
image: deepdaddyttv/weebarr:latest
```

If you are testing locally, this is fine:

```text
WEEBARR_PUBLIC_URL: http://localhost:18080
```

If you expose Weebarr through a domain later, change it to the public URL.

## Start Weebarr

Run:

```bash
cd ~/docker/weebarr
docker compose up -d
```

Open:

```text
http://localhost:18080
```

Then complete the first-run setup and continue to the request-backend step to choose either `Seerr` or `Sonarr Direct`.

## Important Linux Notes

### Keep the config folder mounted

This line keeps your Weebarr data persistent:

```yaml
volumes:
  - ./config:/config
```

Do not remove it unless you are intentionally running a temporary test instance.

### If Seerr is also in Docker

If Seerr is on the same Docker network, use its Docker service name instead of a host IP:

```text
http://seerr:5055
```

### Check folder permissions

Make sure Docker can write to the mounted config folder:

```text
~/docker/weebarr/config
```

If Weebarr starts but cannot save settings, permissions are one of the first things to check.

## Updating Weebarr

From the Weebarr folder, run:

```bash
docker compose pull
docker compose up -d
```

This updates the image while keeping the mounted config folder.

## Backing Up Weebarr

Back up this folder:

```text
~/docker/weebarr/config
```

That folder contains your saved Weebarr state.

## Exposing Weebarr Publicly

If you use HTTPS, a reverse proxy, or a tunnel:

- set `WEEBARR_PUBLIC_URL` to the real public URL
- terminate TLS at the proxy or tunnel
- keep rate limiting and access protections enabled
- avoid exposing the raw container port directly when possible

Example:

```text
https://weebarr.example.com
```
