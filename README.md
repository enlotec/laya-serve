# Laya Serve

Production-ready REST and MCP wrapper for [Laya](https://github.com/NandhaKishorM/laya), Convai Innovations' Apache-2.0, open-source System One decision model. It exposes Laya's typed-decision protocol with explicit readiness, bounded concurrency, typed configuration, and reproducible CPU/GPU containers.

## License

Laya Serve is open-source software licensed under the [Apache License 2.0](LICENSE), the same
permissive license used by Laya. Copyright © enlotec.

## Run locally

Python 3.14 is required.

```powershell
uv venv --python 3.14
uv pip install -e ".[dev]"
enlotec-laya-serve
```

The first run downloads configured Hugging Face checkpoints. The service binds to
`http://localhost:8089`. With the default `LAYA_PRELOAD=true`, startup finishes only after
the configured models have loaded.

## Run with Docker

Choose one of these paths:

| Path | Use it when |
| --- | --- |
| Published image with `docker run` | You want a quick start without cloning or building. |
| Published image with Compose | You want a reusable deployment with an `.env` file. |
| Build from this repository | You want to run your checkout or unpublished changes. |

### Prerequisites

Install and start Docker Engine or Docker Desktop. Use **Linux containers** on Windows.
The Compose files require Docker Compose **2.24.0 or newer** because they use an optional
`env_file`. Python and `uv` are installed inside the image; neither is required on the host.
See Docker's [environment-file documentation](https://docs.docker.com/compose/how-tos/environment-variables/set-environment-variables/).

```console
docker version
docker compose version
```

The first start needs outbound access to Hugging Face to download the checkpoints, plus
enough disk space for the image and model cache and enough RAM for the selected models.
Actual memory use depends on the models and request sizes. CPU is the simplest starting
point. NVIDIA GPU operation additionally needs a compatible driver and Docker GPU support
(NVIDIA Container Toolkit on Linux, or supported WSL2 GPU integration on Windows).

All `docker` commands below are on one line and work in PowerShell, Bash, or a similar shell.

### Option 1: published CPU image with `docker run`

```console
docker pull ghcr.io/enlotec/laya-serve:latest
docker run -d --name laya-serve --restart unless-stopped -p 127.0.0.1:8089:8089 --mount type=volume,source=laya_cache,target=/home/laya/.cache/huggingface -e LAYA_DEVICE=cpu -e LAYA_MODELS=english,multilingual -e LAYA_THREADS=4 ghcr.io/enlotec/laya-serve:latest
docker logs -f laya-serve
```

Press Ctrl+C to stop following logs; the container keeps running. The REST API is available
at `http://localhost:8089` once startup completes. The named volume retains downloaded
models when the container is replaced. The entrypoint prepares cache permissions before
running the service as the `laya` user.

The `127.0.0.1` binding limits access to the Docker host. To allow remote access, change the
mapping to `-p 8089:8089` and configure authentication and your firewall. Docker documents
this behavior in [port publishing](https://docs.docker.com/engine/network/port-publishing/).

For custom settings, create an `.env` file as described below and add `--env-file .env`
**before the image name**. Explicit `-e` arguments override settings from that file.
Keep `LAYA_HOST=0.0.0.0` and `LAYA_PORT=8089` inside the container; to use host port 8090,
change the mapping to `-p 127.0.0.1:8090:8089`.

### Option 2: published CPU image with Compose

Use [`docker-compose.registry.yaml`](docker-compose.registry.yaml). It pulls the published
image and requires no source build. If deploying without a clone, copy that file into an
empty deployment directory; an `.env` file is optional.

From the directory containing the file:

```console
docker compose -f docker-compose.registry.yaml pull
docker compose -f docker-compose.registry.yaml up -d
docker compose -f docker-compose.registry.yaml logs -f laya
```

This file publishes port 8089 on `127.0.0.1`, persists checkpoints in a named volume, and
uses `restart: unless-stopped`. Docker will restart the service after the daemon restarts
unless you deliberately stopped it. See [restart policies](https://docs.docker.com/engine/containers/start-containers-automatically/).

For reproducible deployments, set `LAYA_IMAGE=ghcr.io/enlotec/laya-serve:<published-version>`
in `.env`, replacing the placeholder with an available CPU version tag or image digest.
Also pin `LAYA_REVISION` to a reviewed model revision. `latest` is convenient for evaluation
but can change when a new image is published.

### Option 3: build and run your checkout

Run these commands from the repository root, where `Dockerfile` and `docker-compose.yaml`
are located:

```console
docker compose up -d --build
docker compose logs -f laya
```

The base file builds the `runtime-cpu` Dockerfile target and loads both models by default.
Unlike the registry deployment file, it publishes the host port on all interfaces.
To restrict it to the host, change its `ports` entry to
`"127.0.0.1:${LAYA_PORT:-8089}:8089"`.

To build and run without Compose:

```console
docker build --target runtime-cpu -t laya-serve:local .
docker run -d --name laya-serve-local --restart unless-stopped -p 127.0.0.1:8089:8089 --mount type=volume,source=laya_cache,target=/home/laya/.cache/huggingface -e LAYA_DEVICE=cpu -e LAYA_MODELS=english,multilingual -e LAYA_THREADS=4 laya-serve:local
```

Run only one example on a given host port at a time. Always select `--target runtime-cpu`
for a CPU build: the Dockerfile's final stage is `runtime-gpu`.

### Configuration with `.env`

In a checkout, copy the supplied configuration template:

```powershell
Copy-Item .env.example .env
```

On Bash, use `cp .env.example .env`. For a standalone registry deployment, create `.env`
beside the Compose file with the settings you need. For example:

```dotenv
LAYA_PORT=8089
LAYA_MODELS=english,multilingual
LAYA_PRELOAD=true
LAYA_THREADS=4
LAYA_MAX_CONCURRENT=4
# Uncomment and choose your own value to enable authentication:
# LAYA_API_KEY=replace-with-a-long-random-value
# LAYA_REVISION=reviewed-hugging-face-commit-or-tag
```

Both CPU Compose files load `.env` into the container. Their `environment` entries take
precedence: they enforce the container's host `0.0.0.0`, internal port `8089`, and CPU
device, while interpolating the model, preload, and thread settings. The GPU build override
changes the device to `cuda`. In Compose, `LAYA_PORT` from the host environment or `.env`
selects the **published host port**; the internal port remains 8089 so the image healthcheck
continues to work. With `docker run --env-file`, there is no such port translation.

| Setting | Meaning |
| --- | --- |
| `LAYA_MODELS` | Comma-separated names, e.g. `english,multilingual` or `english`. Use CSV, not a JSON string. |
| `LAYA_PRELOAD` | Defaults to `true`; load configured checkpoints before accepting requests. With `false`, readiness only confirms router initialization, and inference may load models later. |
| `LAYA_THREADS` | CPU PyTorch thread count; Compose defaults to 4. Tune for the host. |
| `LAYA_MAX_CONCURRENT` | Maximum simultaneous inference calls; defaults to 4. Excess calls receive HTTP 503 with `Retry-After: 1`. |
| `LAYA_API_KEY` | Optional bearer token for decision endpoints and MCP HTTP. Diagnostics remain accessible without a token. |
| `LAYA_REVISION` | Optional Hugging Face commit or tag passed to the model router; reported by `/v1/models`. |
| `LAYA_CORS_ORIGINS` | Optional comma-separated browser origins, e.g. `https://your-app.example`. |

See [`.env.example`](.env.example) for request-size and batch limits. Keep `.env` out of
version control (it is already ignored). After changing settings, rerun the appropriate
`docker compose ... up -d` command to recreate the container; a restart alone does not
apply changed container environment variables.

### NVIDIA GPU

Use the GPU image with GPU access and explicitly select CUDA:

```console
docker pull ghcr.io/enlotec/laya-serve:latest-gpu
docker run -d --name laya-serve-gpu --restart unless-stopped --gpus all -p 127.0.0.1:8089:8089 --mount type=volume,source=laya_cache,target=/home/laya/.cache/huggingface -e LAYA_DEVICE=cuda -e LAYA_MODELS=english,multilingual ghcr.io/enlotec/laya-serve:latest-gpu
```

To build the GPU image from this checkout, combine both existing Compose files:

```console
docker compose -f docker-compose.yaml -f docker-compose.gpu.yaml up -d --build
docker compose -f docker-compose.yaml -f docker-compose.gpu.yaml logs -f laya
```

The override selects `runtime-gpu`, sets `LAYA_DEVICE=cuda`, and reserves all NVIDIA GPUs.
The Dockerfile currently installs CUDA 12.8 PyTorch wheels (`TORCH_INDEX=cu128`), so the host
driver must support that runtime. For device reservations, see
[Docker's GPU Compose guide](https://docs.docker.com/compose/how-tos/gpu-support/).

For a **published-image GPU Compose deployment**, save this as `compose.registry-gpu.yaml`
beside `docker-compose.registry.yaml`:

```yaml
services:
  laya:
    image: ghcr.io/enlotec/laya-serve:latest-gpu
    environment:
      LAYA_DEVICE: cuda
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

```console
docker compose -f docker-compose.registry.yaml -f compose.registry-gpu.yaml pull
docker compose -f docker-compose.registry.yaml -f compose.registry-gpu.yaml up -d
```

Use a published GPU version tag or digest in the override to pin the image. Keep the same
`-f` options for later logs, updates, and shutdown commands. The source-build GPU override
contains a `build` section; use the override above with the registry file.

### Verify startup and make a request

The first start may take several minutes for downloads and model loading. During this
startup the HTTP listener may not be available yet. Follow logs and wait for
`laya_engine_ready` and Uvicorn's startup-complete message.

For the registry Compose deployment:

```console
docker compose -f docker-compose.registry.yaml ps
docker compose -f docker-compose.registry.yaml logs --tail 100 laya
```

The image probes `/ready` every 20 seconds, with a 90-second startup grace period.
A slow initial download can outlast that grace period; an unhealthy status alone does not
restart the container. Check logs to distinguish ongoing loading from a startup failure.

Check the service in PowerShell:

```powershell
Invoke-RestMethod http://localhost:8089/health
Invoke-RestMethod http://localhost:8089/ready
Invoke-RestMethod http://localhost:8089/v1/models
```

On Bash, use `curl -fsS http://localhost:8089/ready` (and the other paths similarly).
Look for `status: ready` and the loaded model list. `/health` confirms the HTTP service
responds; `/v1/models` reports configured and loaded models, device setting, and revision.

Send a real decision request in PowerShell:

```powershell
$body = @{
    state = @{ body = "We were billed twice. Please refund us." }
    questions = @{
        department = @{
            type = "choice"
            instructions = "Which team should handle this?"
            criteria = @{ billing = "refunds and payments"; technical = "bugs and outages" }
        }
    }
} | ConvertTo-Json -Depth 10
Invoke-RestMethod -Method Post -Uri http://localhost:8089/v1/systemone -ContentType application/json -Body $body
```

If `LAYA_API_KEY` is enabled, add
`-Headers @{ Authorization = "Bearer <your-key>" }` to the POST command. The HTTP MCP SSE
endpoint is `http://localhost:8089/mcp/sse`, with messages at `/mcp/messages/`; it uses the
same bearer token. The containers start REST and HTTP MCP together.

### Stop, update, and retain the cache

For the registry Compose deployment:

```console
docker compose -f docker-compose.registry.yaml stop
docker compose -f docker-compose.registry.yaml up -d
docker compose -f docker-compose.registry.yaml down
```

`stop` retains the container; `up -d` starts it again. `down` removes containers and the
Compose network but keeps the model-cache volume. Avoid `down -v` unless you deliberately
want to delete the cached checkpoints and download them again. Compose prefixes its
volume name with the project name; this is separate from the plain `laya_cache` volume
used in the `docker run` examples. Keep the same deployment directory/project name to
reuse your Compose cache.

To update a published image while retaining the cache:

```console
docker compose -f docker-compose.registry.yaml pull
docker compose -f docker-compose.registry.yaml up -d
```

For a source build, use `docker compose up -d --build`. For a direct `docker run` deployment,
use `docker stop laya-serve`, `docker rm laya-serve`, pull the desired image, and repeat
the run command with the same volume and settings.

### Troubleshooting

| Symptom | What to check |
| --- | --- |
| GHCR pull says denied or not found | Confirm the tag exists and the package has been made public. For a private package, authenticate with an account that has read access using `docker login ghcr.io`, or build locally. |
| `port is already allocated` | Stop the other service or choose another host port. For Compose, set `LAYA_PORT=8090` in `.env`; for `docker run`, change only the host side of the mapping. |
| Connection refused during startup | Follow logs; checkpoint downloads and preloading finish before HTTP startup. Check outbound access to Hugging Face and disk space. |
| Container exits or keeps restarting | Inspect logs for checkpoint, configuration, or permission errors. The wrapper fails startup if required model loading fails. |
| Exit code 137 / `OOMKilled` | Inspect the container's state and host memory limits. Increase available memory or load fewer models, e.g. `LAYA_MODELS=english`. Lower concurrency for inference memory pressure. |
| CUDA unavailable / GPU driver selection error | Check the NVIDIA driver and Docker GPU integration; use the GPU image and `--gpus all` or the GPU Compose reservation. CPU images cannot provide CUDA execution. |
| HTTP 401 on a prediction or MCP request | Supply `Authorization: Bearer <your-key>` matching `LAYA_API_KEY`. |
| HTTP 503 during inference | All inference slots are occupied. Retry after the response's `Retry-After` interval or tune concurrency within your memory budget. |

For a direct container, `docker inspect --format '{{json .State}}' laya-serve` shows health,
exit status, and OOM information. For Compose, obtain its ID with
`docker compose -f docker-compose.registry.yaml ps -a -q laya`, then inspect that ID.

## Container images

GitHub Actions publishes images to GitHub Container Registry when changes reach `main` and when a
version tag is pushed:

```bash
docker pull ghcr.io/enlotec/laya-serve:latest
docker pull ghcr.io/enlotec/laya-serve:latest-gpu
```

Version tags such as `v0.1.0` also publish `0.1.0` and `0.1` CPU tags plus `0.1.0-gpu` and
`0.1-gpu` GPU tags. The images are public only after the GitHub package visibility is set to
public for the first published version.

## HTTP API

`POST /v1/systemone` accepts Laya's typed-decision request and response shape:

```json
{
  "state": {"body": "We were billed twice. Please refund us."},
  "questions": {
    "department": {
      "type": "choice",
      "instructions": "Which team should handle this?",
      "criteria": {"billing": "refunds and payments", "technical": "bugs and outages"}
    },
    "urgency": {
      "type": "score",
      "instructions": "How urgent is this?",
      "criteria": ["low", "normal", "critical"]
    },
    "churn_risk": {
      "type": "noul",
      "instructions": "Does the customer threaten to cancel?"
    }
  }
}
```

`POST /v1/systemone/batch` accepts the same `questions` with `states`. `GET /health`, `GET /ready`, and `GET /v1/models` are available for operations.

Use `LAYA_API_KEY` to require `Authorization: Bearer <key>`. Settings are documented in [`.env.example`](.env.example).
Set `LAYA_REVISION` to a reviewed Hugging Face commit or tag in a production deployment; the
selected revision is included in `GET /v1/models`.
Set `LAYA_MODELS` to a comma-separated list such as `english,multilingual`.

## MCP

Run the stdio MCP server with:

```powershell
enlotec-laya-serve-mcp
```

It provides `laya_predict` and `laya_status`, sharing the same Laya configuration and validation as REST.
The HTTP SSE transport is mounted at `http://localhost:8089/mcp/sse` (messages:
`/mcp/messages/`). When `LAYA_API_KEY` is configured, both REST and MCP HTTP requests require
the bearer token.

## Development

```powershell
uv run pytest
uv run ruff check .
```

This package intentionally fails startup if real Laya checkpoints cannot load; it never synthesizes model responses.

## Acknowledgment

Thank you to the [Laya team](https://github.com/NandhaKishorM/laya) at Convai Innovations for
creating and maintaining the open-source Laya decision model that powers this service.
