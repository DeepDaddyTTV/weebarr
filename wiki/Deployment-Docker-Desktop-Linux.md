# Deploying on Docker Desktop for Linux

## Prerequisites

- Docker Desktop for Linux
- A running Seerr instance
- A Seerr API key
- A persistent folder for Weebarr config

## Recommended Folder Layout

Example:

```text
~/docker/weebarr/
├── compose.yml
└── config/
```

## Example Compose File

```yaml
services:
  weebarr:
    image: ghcr.io/deepdaddyttv/weebarr:latest
    container_name: weebarr
    environment:
      TZ: UTC
      WEEBARR_PUBLIC_URL: http://localhost:8080
      SEERR_BASE_URL: http://seerr:5055
      SEERR_API_KEY: change-me
      SEERR_REQUEST_SEASONS: all
    ports:
      - "8080:8888"
    volumes:
      - ./config:/config
    restart: unless-stopped
```

## First Startup

```bash
cd ~/docker/weebarr
docker compose up -d
```

Open:

```text
http://localhost:8080
```

Then complete first-run setup.

## Linux Notes

- Keep the config bind mounted.
- If Seerr is containerized on the same Docker network, use its service name rather than a host IP.
- Make sure the mounted config path is writable by Docker.

## Updating

```bash
docker compose pull
docker compose up -d
```

## Backup

Back up:

```text
~/docker/weebarr/config
```

## Public Exposure

When using HTTPS, a reverse proxy, or a tunnel:

- set `WEEBARR_PUBLIC_URL`
- terminate TLS at the proxy
- keep edge rate limits and auth protections enabled

