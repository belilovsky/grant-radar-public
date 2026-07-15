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
PUBLIC_URL="${PUBLIC_URL:-}"
REQUIRE_PUBLIC_VERIFY="${REQUIRE_PUBLIC_VERIFY:-1}"

cd "$ROOT_DIR"

if [[ -z "$DEPLOY_HOST" ]]; then
  echo "DEPLOY_HOST is not set. Example: export DEPLOY_HOST=deploy@example.org" >&2
  exit 2
fi

if [[ "$REQUIRE_PUBLIC_VERIFY" == "1" && -z "$PUBLIC_URL" ]]; then
  echo "PUBLIC_URL is required for end-to-end production verification." >&2
  echo "Set REQUIRE_PUBLIC_VERIFY=0 only for an intentionally private target." >&2
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
  export APP_REVISION='$REVISION'
  export APP_DEPLOYED_AT='$DEPLOYED_AT'
  docker compose --env-file '$ENV_FILE' $COMPOSE_FILES up -d --build
  ready_ok=0
  for attempt in \$(seq 1 '$READY_ATTEMPTS'); do
    if docker compose --env-file '$ENV_FILE' $COMPOSE_FILES exec -T api \
      curl -fsS '$READY_URL' >/dev/null 2>&1; then
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

if [[ -n "$PUBLIC_URL" ]]; then
  release_url="${PUBLIC_URL%/}/.well-known/release.json?revision=$REVISION"
  public_revision="$(
    curl -fsS --retry 5 --retry-delay 2 "$release_url" |
      python3 -c 'import json, sys; print(json.load(sys.stdin).get("revision", ""))'
  )"
  if [[ "$public_revision" != "$REVISION" ]]; then
    echo "Public revision mismatch: got '$public_revision', expected '$REVISION'." >&2
    echo "The target may not be connected to the public route." >&2
    exit 1
  fi
  echo "Public revision verified at ${PUBLIC_URL%/}: $REVISION"
fi

echo "Deployed $REVISION to $DEPLOY_HOST:$DEPLOY_PATH at $DEPLOYED_AT"
