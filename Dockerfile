# syntax=docker/dockerfile:1
FROM python:3.14-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    USE_TF=0 \
    HF_HOME=/home/laya/.cache/huggingface

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock README.md /app/

FROM base AS cpu
RUN uv pip install --system --no-cache torch --index-url https://download.pytorch.org/whl/cpu
COPY laya_serve /app/laya_serve
RUN uv pip install --system --no-cache .

FROM cpu AS runtime-cpu
RUN useradd --create-home --uid 10001 laya && chown -R laya:laya /app /home/laya
USER laya
EXPOSE 8089
HEALTHCHECK --interval=20s --timeout=5s --retries=3 --start-period=90s CMD curl --fail http://localhost:8089/ready || exit 1
ENTRYPOINT ["enlotec-laya-serve"]

FROM base AS gpu
ARG TORCH_INDEX=cu128
RUN uv pip install --system --no-cache torch --index-url https://download.pytorch.org/whl/${TORCH_INDEX}
COPY laya_serve /app/laya_serve
RUN uv pip install --system --no-cache .

FROM gpu AS runtime-gpu
ENV TORCH_DISABLE_NATIVE_JIT=1
RUN useradd --create-home --uid 10001 laya && chown -R laya:laya /app /home/laya
USER laya
EXPOSE 8089
HEALTHCHECK --interval=20s --timeout=5s --retries=3 --start-period=90s CMD curl --fail http://localhost:8089/ready || exit 1
ENTRYPOINT ["enlotec-laya-serve"]
