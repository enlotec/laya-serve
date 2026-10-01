#!/bin/sh
set -eu

cache_dir="${HF_HOME:-/home/laya/.cache/huggingface}"
mkdir -p "$cache_dir"

# Docker creates a fresh named volume as root.  Give the unprivileged service
# user access before Hugging Face downloads model files into the mounted cache.
if [ "$(stat -c %u "$cache_dir")" != "$(id -u laya)" ]; then
    chown -R laya:laya "$cache_dir"
fi

exec setpriv --reuid=laya --regid=laya --init-groups "$@"
