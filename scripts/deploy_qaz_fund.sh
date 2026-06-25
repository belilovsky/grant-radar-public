#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEPLOY_HOST="${DEPLOY_HOST:-}"
DEPLOY_PATH="${DEPLOY_PATH:-/opt/grant-radar}"
COMPOSE_FILES="${COMPOSE_FILES:--f docker-compose.yml -f docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-.env.prod}"

cd "$ROOT_DIR"

if [[ -z "$DEPLOY_HOST" ]]; then
  echo "DEPLOY_HOST is not set. Example: export DEPLOY_HOST=deploy@example.org" >&2
  exit 2
fi

if [[ -n "$(git status --short)" ]]; then
  echo "Refusing to deploy with a dirty working tree." >&2
  git status --short >&2
  exit 1
fi

REVISION="$(git rev-parse HEAD)"
DEPLOYED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

rsync -az --delete \
  --exclude ".git" \
  --exclude ".venv" \
  --exclude "__pycache__" \
  --exclude ".pytest_cache" \
  --exclude ".mypy_cache" \
  "$ROOT_DIR/" "$DEPLOY_HOST:$DEPLOY_PATH/"

ssh "$DEPLOY_HOST" "
  set -euo pipefail
  cd '$DEPLOY_PATH'
  docker compose --env-file '$ENV_FILE' $COMPOSE_FILES up -d --build
  printf '%s\n' '$REVISION' > .deployed-revision
  printf '%s\n' '$DEPLOYED_AT' > .deployed-at
  docker compose --env-file '$ENV_FILE' $COMPOSE_FILES ps
"

echo "Deployed $REVISION to $DEPLOY_HOST:$DEPLOY_PATH at $DEPLOYED_AT"
