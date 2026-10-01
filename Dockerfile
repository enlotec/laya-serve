# syntax=docker/dockerfile:1
FROM python:3.14-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_HTTP_TIMEOUT=300 \
    USE_TF=0 \
    HF_HOME=/home/laya/.cache/huggingface

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

FROM base AS build-cpu
WORKDIR /build
COPY pyproject.toml uv.lock README.md /build/
RUN uv pip install --system --no-cache torch --index-url https://download.pytorch.org/whl/cpu
COPY laya_serve /build/laya_serve
RUN uv pip install --system --no-cache .

FROM base AS runtime-cpu
COPY --from=build-cpu /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=build-cpu /usr/local/bin/enlotec-laya-serve /usr/local/bin/enlotec-laya-serve
RUN useradd --create-home --uid 10001 laya
USER laya
EXPOSE 8089
HEALTHCHECK --interval=20s --timeout=5s --retries=3 --start-period=90s CMD curl --fail http://localhost:8089/ready || exit 1
ENTRYPOINT ["enlotec-laya-serve"]

FROM base AS build-gpu
WORKDIR /build
COPY pyproject.toml uv.lock README.md /build/
ARG TORCH_INDEX=cu128
RUN uv pip install --system --no-cache torch --index-url https://download.pytorch.org/whl/${TORCH_INDEX}
COPY laya_serve /build/laya_serve
RUN uv pip install --system --no-cache .

FROM base AS runtime-gpu
ENV TORCH_DISABLE_NATIVE_JIT=1
COPY --from=build-gpu /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=build-gpu /usr/local/bin/enlotec-laya-serve /usr/local/bin/enlotec-laya-serve
RUN useradd --create-home --uid 10001 laya
USER laya
EXPOSE 8089
HEALTHCHECK --interval=20s --timeout=5s --retries=3 --start-period=90s CMD curl --fail http://localhost:8089/ready || exit 1
ENTRYPOINT ["enlotec-laya-serve"]
