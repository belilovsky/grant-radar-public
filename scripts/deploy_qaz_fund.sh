#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEPLOY_HOST="${DEPLOY_HOST:-}"
DEPLOY_PATH="${DEPLOY_PATH:-/opt/grant-radar}"
COMPOSE_FILES="${COMPOSE_FILES:--f docker-compose.yml -f docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-.env.prod}"
RSYNC_DELETE="${RSYNC_DELETE:-0}"
READY_URL="${READY_URL:-http://127.0.0.1:8000/ready}"
READY_ATTEMPTS="${READY_ATTEMPTS:-30}"
READY_DELAY="${READY_DELAY:-2}"

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

RSYNC_ARGS=(
  -az
  --exclude ".git"
  --exclude ".venv"
  --exclude "__pycache__"
  --exclude ".pytest_cache"
  --exclude ".mypy_cache"
)

if [[ "$RSYNC_DELETE" == "1" ]]; then
  RSYNC_ARGS+=(--delete)
fi

rsync "${RSYNC_ARGS[@]}" "$ROOT_DIR/" "$DEPLOY_HOST:$DEPLOY_PATH/"

ssh "$DEPLOY_HOST" "
  set -euo pipefail
  cd '$DEPLOY_PATH'
  docker compose --env-file '$ENV_FILE' $COMPOSE_FILES up -d --build
  ready_ok=0
  for attempt in \$(seq 1 '$READY_ATTEMPTS'); do
    if docker compose --env-file '$ENV_FILE' $COMPOSE_FILES exec -T api \
      curl -fsS '$READY_URL' >/dev/null; then
      ready_ok=1
      break
    fi
    sleep '$READY_DELAY'
  done
  if [[ \"\$ready_ok\" != \"1\" ]]; then
    echo 'API readiness check failed after deploy.' >&2
    docker compose --env-file '$ENV_FILE' $COMPOSE_FILES logs --tail=80 api >&2 || true
    exit 1
  fi
  printf '%s\n' '$REVISION' > .deployed-revision
  printf '%s\n' '$DEPLOYED_AT' > .deployed-at
  docker compose --env-file '$ENV_FILE' $COMPOSE_FILES ps
"

echo "Deployed $REVISION to $DEPLOY_HOST:$DEPLOY_PATH at $DEPLOYED_AT"
