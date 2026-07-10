#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
docker compose -f docker/docker-compose.yml -f docker/docker-compose.hive.yml up -d
docker compose -f docker/docker-compose.yml -f docker/docker-compose.hive.yml ps
