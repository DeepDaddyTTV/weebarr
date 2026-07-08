---
layout: default
title: Update Container
---

# Update Container

When Weebarr detects that Docker Hub has a newer published image than the one your container is running, it now shows a yellow **New version available!** card in the sidebar. Clicking that card opens this page.

The safe update flow is the same whether you use Seerr or Sonarr Direct:

1. Back up your mounted `/config` data.
2. Pull the latest `deepdaddyttv/weebarr` image.
3. Recreate the container with the same mounted config and port mapping.
4. Wait for the container to go healthy.
5. Open Weebarr and confirm your selected backend still connects.

## Before You Update

- Keep your `/config` mount in place so Weebarr keeps its auth, backend, automation, and theme settings.
- If you changed public URLs, reverse-proxy rules, or backend hostnames recently, verify those first before assuming the image update caused any problem.
- Existing installs keep the current request backend selection. A Seerr install stays on Seerr. A Sonarr Direct install stays on Sonarr Direct.

## Portainer

If you run Weebarr through Portainer:

1. Open the Weebarr container or stack.
2. Pull the newest image for `deepdaddyttv/weebarr`.
3. Recreate or update the container without removing the `/config` volume.
4. Wait for the health check to pass.
5. Open the app and confirm the sidebar connection card still shows the expected backend as connected.

## Docker CLI

If you manage the container directly:

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

Adjust the container name, published port, and config path to match your setup.

## Docker Compose

If you use Compose:

```bash
docker compose pull
docker compose up -d
```

Then confirm the container recreated successfully and still uses the same mounted `/config` path.

## Verify the Update

Check the health endpoint:

```text
/api/health
```

You should see the new version reported there. After that:

- open the Seasonal page
- verify the sidebar connection card still shows the correct backend
- open **Settings > Connections** if you want to run the live backend validation again

## If the App Starts but Requests Fail

That usually means the container update worked, but the live backend details need attention.

Check:

- the selected backend in **Settings**
- the Seerr or Sonarr Direct connection values
- whether the backend host is still reachable from the Weebarr container
- whether API keys were rotated on the backend side

If needed, use the backend-specific connection test in Settings after the update.
