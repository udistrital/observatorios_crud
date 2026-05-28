#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$ROOT_DIR/osiris"
ENV_FILE="$APP_DIR/.env"
ENV_EXAMPLE="$APP_DIR/.env.template"

if [[ ! -f "$ENV_FILE" ]]; then
  if [[ -f "$ENV_EXAMPLE" ]]; then
    cp "$ENV_EXAMPLE" "$ENV_FILE"
    echo "Se creo $ENV_FILE desde .env.template"
    echo "Usando valores por defecto; revisa $ENV_FILE si es necesario."
  else
    echo "No existe $ENV_FILE ni $ENV_EXAMPLE"
    exit 1
  fi
fi

echo "Levantando solo API CRUD..."
docker compose -f "$APP_DIR/docker-compose.yml" up  --build
# docker compose -f "$APP_DIR/docker-compose.yml" ps
