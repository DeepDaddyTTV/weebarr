# Other Deployment Options

## 1. Native Docker Compose on Linux

If you do not use Docker Desktop, Weebarr works the same way with standard Docker Engine plus Compose.

Minimal pattern:

```yaml
services:
  weebarr:
    image: ghcr.io/deepdaddyttv/weebarr:latest
    environment:
      WEEBARR_PUBLIC_URL: https://weebarr.example.com
      SEERR_BASE_URL: http://seerr:5055
      SEERR_API_KEY: change-me
    ports:
      - "18080:8888"
    volumes:
      - /opt/weebarr/config:/config
    restart: unless-stopped
```

## 2. Portainer Stack

Weebarr can be deployed as a normal Portainer stack service.

Recommended approach:

- keep the image generic
- mount `/config`
- store secrets in stack env vars or Portainer secrets
- set `WEEBARR_PUBLIC_URL` when exposing through a public hostname

## 3. Reverse Proxy Deployment

Common reverse proxy choices:

- Nginx Proxy Manager
- Caddy
- Traefik

Recommended edge behavior:

- HTTPS only
- HSTS if you want strict TLS
- rate limiting
- optional extra auth in front of Weebarr

## 4. Cloudflare Tunnel

Weebarr works behind Cloudflare Tunnel.

If you do this:

- set `WEEBARR_PUBLIC_URL` to the real public URL
- keep the app behind Cloudflare TLS
- keep Cloudflare rate limiting and abuse protections on

## 5. Bare Python Runtime

This is mainly for development, not the primary production target.

Example:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
WEEBARR_PUBLIC_URL=http://localhost:18080 \
SEERR_BASE_URL=http://localhost:5055 \
SEERR_API_KEY=change-me \
python -m src.main
```

## 6. Custom Images or Forked Builds

If you build your own image:

- keep runtime configuration environment-driven
- do not bake private URLs or keys into the image
- still mount `/config` for persistence

## Upgrade Strategy

Regardless of platform:

1. back up the config volume
2. pull the new image
3. recreate the container
4. verify `/api/health`
5. confirm the UI and Seerr integration still work
