#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$ROOT_DIR/osiris"
ENV_FILE="$APP_DIR/.env"
ENV_EXAMPLE="$APP_DIR/.env.template"

ensure_document_reference_key() {
  local current_key=""
  local parameter_store=""
  local generated_key
  local temporary_file
  local key_replaced=false
  local line

  while IFS= read -r line || [[ -n "$line" ]]; do
    case "$line" in
      DOCUMENT_REFERENCE_KEY=*|export\ DOCUMENT_REFERENCE_KEY=*)
        current_key="${line#*=}"
        ;;
      PARAMETER_STORE=*|export\ PARAMETER_STORE=*)
        parameter_store="${line#*=}"
        ;;
    esac
  done < "$ENV_FILE"

  if [[ "$current_key" =~ ^[A-Za-z0-9_-]{43}=$ ]]; then
    return
  fi

  if [[ -n "$parameter_store" ]]; then
    echo "DOCUMENT_REFERENCE_KEY debe configurarse con una clave Fernet valida."
    exit 1
  fi

  generated_key="$(python3 -c 'import base64, secrets; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii"))')"
  temporary_file="$(mktemp "${ENV_FILE}.tmp.XXXXXX")"
  chmod 600 "$temporary_file"

  while IFS= read -r line || [[ -n "$line" ]]; do
    if [[ "$line" == DOCUMENT_REFERENCE_KEY=* \
      || "$line" == "export DOCUMENT_REFERENCE_KEY="* ]]; then
      printf 'DOCUMENT_REFERENCE_KEY=%s\n' "$generated_key" >> "$temporary_file"
      key_replaced=true
    else
      printf '%s\n' "$line" >> "$temporary_file"
    fi
  done < "$ENV_FILE"

  if [[ "$key_replaced" == false ]]; then
    printf '\nDOCUMENT_REFERENCE_KEY=%s\n' "$generated_key" >> "$temporary_file"
  fi

  mv "$temporary_file" "$ENV_FILE"
  chmod 600 "$ENV_FILE"
  echo "Se genero una clave Fernet local en $ENV_FILE."
}

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

ensure_document_reference_key

if [[ "${1:-}" == "--prepare-env" ]]; then
  echo "Configuracion local preparada."
  exit 0
fi

echo "Levantando solo API CRUD..."
docker compose -f "$APP_DIR/docker-compose.yml" up  --build
# docker compose -f "$APP_DIR/docker-compose.yml" ps
