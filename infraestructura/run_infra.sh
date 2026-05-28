#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$ROOT_DIR"
NETWORK_NAME="elastic_net"

if ! docker network inspect "$NETWORK_NAME" >/dev/null 2>&1; then
  echo "Creando red Docker $NETWORK_NAME..."
  docker network create "$NETWORK_NAME" >/dev/null
fi

echo "Levantando solo infraestructura (Elasticsearch, Kibana, Nginx)..."
docker compose -f "$INFRA_DIR/docker-compose.yml" up -d
docker compose -f "$INFRA_DIR/docker-compose.yml" ps
