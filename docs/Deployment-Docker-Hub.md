---
title: Docker Hub
---

# Installing From Docker Hub

If you prefer Docker Hub over GitHub Container Registry, Weebarr is intended to be available there as:

```text
deepdaddyttv/weebarr
```

Use this page if you already know how you want to run Weebarr and only need the Docker Hub image reference and example commands.

## Docker Hub Repository

- [Weebarr on Docker Hub](https://hub.docker.com/repository/docker/deepdaddyttv/weebarr/general)

## Quick Pull

Pull the latest published image:

```bash
docker pull deepdaddyttv/weebarr:latest
```

Pull a specific version:

```bash
docker pull deepdaddyttv/weebarr:0.1.43
```

## Using Docker Desktop UI

If you are using Docker Desktop, you can pull Weebarr directly from the app instead of using the terminal.

1. Open Docker Desktop.
2. Go to `Images`.
3. Use the pull or search field and enter:

   ```text
   deepdaddyttv/weebarr:latest
   ```

   or a specific version such as:

   ```text
   deepdaddyttv/weebarr:0.1.43
   ```

4. Pull the image.
5. Either create a container from that image in Docker Desktop or use it in a Compose stack.

Even when you pull through the UI, Weebarr still needs:

- a mounted `/config` folder
- your Seerr connection values
- a port mapping such as `18080:8888`

## Compose Example

If you are using Docker Compose, the only required difference is the image line:

```yaml
services:
  weebarr:
    image: deepdaddyttv/weebarr:latest
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

Open the app at:

```text
http://localhost:18080
```

## Docker Run Example

If you prefer `docker run`:

```bash
docker run -d \
  --name weebarr \
  -p 18080:8888 \
  -e TZ=UTC \
  -e WEEBARR_PUBLIC_URL=http://localhost:18080 \
  -e SEERR_BASE_URL=http://seerr:5055 \
  -e SEERR_API_KEY=change-me \
  -e SEERR_REQUEST_SEASONS=all \
  -v $(pwd)/config:/config \
  --restart unless-stopped \
  deepdaddyttv/weebarr:latest
```

## When To Use Docker Hub Instead Of GHCR

Docker Hub can be the better fit if:

- your server already mirrors or trusts Docker Hub by default
- your deployment platform expects Docker Hub images first
- you want a shorter image name in examples or scripts

GHCR is still fully supported. Pick the registry that fits your environment better.

## Related Guides

- [Docker Desktop on Windows](Deployment-Docker-Desktop-Windows.md)
- [Docker Desktop on Linux](Deployment-Docker-Desktop-Linux.md)
- [Other Deployment Options](Deployment-Other-Options.md)
- [Troubleshooting](Troubleshooting.md)
