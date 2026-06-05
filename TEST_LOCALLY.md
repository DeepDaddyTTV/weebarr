# Testing Weebarr Locally

## Python

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
WEEBARR_PORT=8080 SEERR_BASE_URL=http://localhost:5055 SEERR_API_KEY=change-me python -m src.main
```

Open `http://localhost:8080`.

## Docker

```bash
docker build -t weebarr:test .
docker run --rm \
  --name weebarr \
  -p 8080:8888 \
  -e SEERR_BASE_URL=http://host.docker.internal:5055 \
  -e SEERR_API_KEY=change-me \
  weebarr:test
```

Open `http://localhost:8080`.

## Public Image

```bash
docker run --rm \
  --name weebarr \
  -p 8080:8888 \
  -e SEERR_BASE_URL=http://host.docker.internal:5055 \
  -e SEERR_API_KEY=change-me \
  ghcr.io/deepdaddyttv/weebarr:latest
```

## Smoke Checks

```bash
curl http://localhost:8080/api/health
curl "http://localhost:8080/api/seasonal?season=SPRING&year=2026&perPage=5"
```
