# Update Container

When Weebarr detects that Docker Hub has a newer published image than the container you are running, it can show a yellow **New version available!** card in the sidebar. Clicking that card opens the update guide.

## Safe Update Flow

1. Back up the mounted `/config` data.
2. Pull the latest `deepdaddyttv/weebarr` image.
3. Recreate the container without changing the config mount.
4. Wait for the health check to pass.
5. Open Weebarr and confirm the selected backend still connects.

This works the same whether your request backend is Seerr or Sonarr Direct.

## Portainer

If you update through Portainer:

1. Open the Weebarr stack or container.
2. Pull the latest image.
3. Recreate or redeploy the service while preserving `/config`.
4. Wait for the container to become healthy.
5. Open the UI and confirm the sidebar connection card still shows the expected backend.

## Docker CLI

```bash
docker pull deepdaddyttv/weebarr:latest
docker stop weebarr
docker rm weebarr
docker run -d \
  --name weebarr \
  -p 18080:8888 \
  -v /path/to/weebarr-config:/config \
  --restart unless-stopped \
  deepdaddyttv/weebarr:latest
```

Adjust the container name, published port, and config path to match your environment.

## Docker Compose

```bash
docker compose pull
docker compose up -d
```

## Verify After Updating

Use:

```text
/api/health
```

Then verify:

- the reported version is the new one
- the Seasonal page loads cleanly
- the selected request backend still connects
- backend validation still passes in Settings if you rerun it
