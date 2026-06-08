# Deploying on Docker Desktop for Windows

## Prerequisites

- Docker Desktop for Windows
- A working Seerr instance
- A Seerr API key
- A folder on Windows to store Weebarr config

## Recommended Folder Layout

Example:

```text
C:\\Docker\\Weebarr
├── compose.yml
└── config\\
```

## Example Compose File

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

## First Startup

1. Open a terminal in `C:\\Docker\\Weebarr`
2. Run:

```powershell
docker compose up -d
```

3. Open:

```text
http://localhost:18080
```

4. Complete the first-run setup:
   - local auth
   - Plex auth
   - or both

## Windows Notes

- Use forward slashes in Compose bind mounts when possible.
- Keep the config directory mounted so Weebarr settings persist across upgrades.
- If Seerr is running in Docker too, prefer Docker network hostnames like `http://seerr:5055` instead of Windows host IPs.
- If Seerr is outside Docker Desktop, use a URL reachable from inside the container.

## Updating

```powershell
docker compose pull
docker compose up -d
```

## Backup

Back up the mounted config directory:

```text
C:\\Docker\\Weebarr\\config
```

That preserves:

- access settings
- saved Seerr integration settings
- automation history
- theme imports
- Weebarr request history

## Public Exposure

If you expose Weebarr through a reverse proxy, tunnel, or HTTPS endpoint:

- set `WEEBARR_PUBLIC_URL` to the public URL
- keep TLS and rate limiting at the edge
- avoid exposing the raw container port directly when possible
