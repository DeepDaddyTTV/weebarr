---
title: Other Deployment Options
---

# Other Deployment Options

This page covers ways to run Weebarr outside the basic Docker Desktop guides.

If you are new to Docker, use one of these first:

- [Docker Desktop on Windows](Deployment-Docker-Desktop-Windows.md)
- [Docker Desktop on Linux](Deployment-Docker-Desktop-Linux.md)

## Image Registries

Weebarr is intended to be available from both:

- `ghcr.io/deepdaddyttv/weebarr`
- `deepdaddyttv/weebarr`

Use whichever registry fits your environment better.

## Native Docker Compose on Linux

If you use Docker Engine directly, Weebarr runs normally with Docker Compose.

Example compose file:

```yaml
services:
  weebarr:
    image: ghcr.io/deepdaddyttv/weebarr:latest
    container_name: weebarr
    environment:
      TZ: UTC
      WEEBARR_PUBLIC_URL: https://weebarr.example.com
      SEERR_BASE_URL: http://seerr:5055
      SEERR_API_KEY: change-me
      SEERR_REQUEST_SEASONS: all
    ports:
      - "18080:8888"
    volumes:
      - /opt/weebarr/config:/config
    restart: unless-stopped
```

If you want Docker Hub instead, change the image to:

```yaml
image: deepdaddyttv/weebarr:latest
```

Before starting, change:

- `TZ`
- `WEEBARR_PUBLIC_URL`
- `SEERR_BASE_URL`
- `SEERR_API_KEY`

Start it with:

```bash
docker compose up -d
```

## Portainer Stack

Weebarr can be deployed as a normal Portainer stack.

Recommended approach:

- use the published Weebarr image
- mount `/config` so settings persist
- store secrets as environment variables or Portainer secrets
- set `WEEBARR_PUBLIC_URL` if using a public hostname

The important part is still the config mount:

```yaml
volumes:
  - /opt/weebarr/config:/config
```

Without that, your settings may not survive container recreation.

## Reverse Proxy

Weebarr can sit behind a reverse proxy.

Common options include:

- Nginx Proxy Manager
- Caddy
- Traefik

Recommended setup:

- use HTTPS
- point the proxy to Weebarr's internal port
- set `WEEBARR_PUBLIC_URL` to the public URL users will actually visit
- keep rate limiting or extra access protection enabled if possible

Example public URL:

```text
https://weebarr.example.com
```

If Plex login behaves strangely, double-check that `WEEBARR_PUBLIC_URL` matches the public address exactly.

## Cloudflare Tunnel

Weebarr works behind Cloudflare Tunnel.

If you use a tunnel:

- set `WEEBARR_PUBLIC_URL` to the real public URL
- keep Cloudflare TLS enabled
- keep Cloudflare rate limiting and abuse protections enabled
- forward traffic to the Weebarr container port

Example:

```text
https://weebarr.example.com
```

The public URL matters because login flows and callbacks need to know the outside address.

## Bare Python Runtime

Running Weebarr directly with Python is mainly for development.

Most users should use Docker instead.

Example development pattern:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
WEEBARR_PUBLIC_URL=http://localhost:18080 \
SEERR_BASE_URL=http://localhost:5055 \
SEERR_API_KEY=change-me \
WEEBARR_PORT=18080 \
python -m src.main
```

Use this only if you are working on the app or testing code changes.

## Custom Images or Forked Builds

If you build your own image:

- keep private URLs and keys out of the image
- pass runtime values through environment variables
- still mount `/config`
- avoid hardcoding anything that changes between users or servers

A container image should be reusable. Your private setup belongs in environment variables and mounted config, not baked into the image.

## Upgrade Strategy

No matter how you deploy Weebarr, the safe upgrade flow is:

1. Back up the config volume.
2. Pull the new image.
3. Recreate the container.
4. Check the health endpoint.
5. Open the UI and confirm Seerr still connects.

Health check:

```text
/api/health
```

If the app starts but requests fail, check the **Connections** tab and run the Seerr connection test.
