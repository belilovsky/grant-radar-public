#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEPLOY_HOST="${DEPLOY_HOST:-}"
DEPLOY_PATH="${DEPLOY_PATH:-/opt/grant-radar}"
COMPOSE_FILES="${COMPOSE_FILES:--f docker-compose.yml -f docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-.env.prod}"
READY_URL="${READY_URL:-http://127.0.0.1:8000/ready}"
READY_ATTEMPTS="${READY_ATTEMPTS:-30}"
READY_DELAY="${READY_DELAY:-2}"
SEMANTIC_READY_ATTEMPTS="${SEMANTIC_READY_ATTEMPTS:-450}"
SEMANTIC_READY_DELAY="${SEMANTIC_READY_DELAY:-2}"
WORKER_READY_ATTEMPTS="${WORKER_READY_ATTEMPTS:-120}"
WORKER_READY_DELAY="${WORKER_READY_DELAY:-2}"
PUBLIC_URL="${PUBLIC_URL:-}"
REQUIRE_PUBLIC_VERIFY="${REQUIRE_PUBLIC_VERIFY:-1}"
MIN_FREE_BYTES="${MIN_FREE_BYTES:-21474836480}"
SOURCE_BACKUP_ROOT="${SOURCE_BACKUP_ROOT:-/var/backups/grant-radar/source-sync}"
RECONCILE_SOURCE_DUMP="${RECONCILE_SOURCE_DUMP:-}"
RECONCILE_SOURCE_DUMP_SHA256="${RECONCILE_SOURCE_DUMP_SHA256:-}"
RECONCILE_EXPECTED_SOURCE_COUNT="${RECONCILE_EXPECTED_SOURCE_COUNT:-}"
RECONCILE_EXPECTED_TARGET_COUNT="${RECONCILE_EXPECTED_TARGET_COUNT:-}"

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
BUILT_AT="$DEPLOYED_AT"
RELEASE_STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
if command -v sha256sum >/dev/null 2>&1; then
  ARTIFACT_DIGEST="sha256:$(git archive "$REVISION" | sha256sum | awk '{print $1}')"
else
  ARTIFACT_DIGEST="sha256:$(git archive "$REVISION" | shasum -a 256 | awk '{print $1}')"
fi

run_remote_capacity_preflight() {
  local remote_command
  printf -v remote_command \
    'env DEPLOY_PATH=%q ENV_FILE=%q COMPOSE_FILES=%q MIN_FREE_BYTES=%q bash -s' \
    "$DEPLOY_PATH" "$ENV_FILE" "$COMPOSE_FILES" "$MIN_FREE_BYTES"
  ssh "$DEPLOY_HOST" "$remote_command" <<'QAZ_FUND_CAPACITY_PREFLIGHT'
set -euo pipefail

root_dir="${DEPLOY_PATH:-/opt/grant-radar}"
env_file="${ENV_FILE:-.env.prod}"
compose_files="${COMPOSE_FILES:--f docker-compose.yml -f docker-compose.prod.yml}"
min_free_bytes="${MIN_FREE_BYTES:-21474836480}"
cd "$root_dir"

current_api_image="$(docker compose --env-file "$env_file" $compose_files images -q api 2>/dev/null | head -n 1)"
current_semantic_image="$(docker compose --env-file "$env_file" $compose_files images -q semantic 2>/dev/null | head -n 1)"
if [[ -z "$current_api_image" || -z "$current_semantic_image" ]]; then
  echo "QAZ.FUND preflight rollback gate failed: current images are missing." >&2
  exit 74
fi

image_size() {
  local image_id="$1"
  if [[ -z "$image_id" ]]; then
    printf '0\n'
    return
  fi
  docker image inspect --format '{{.Size}}' "$image_id" 2>/dev/null || printf '0\n'
}

current_bytes="$(( $(image_size "$current_api_image") + $(image_size "$current_semantic_image") ))"
required_bytes="$(( 2 * (current_bytes + current_bytes) ))"
if (( required_bytes < min_free_bytes )); then
  required_bytes="$min_free_bytes"
fi
free_bytes="$(df -PB1 "$root_dir" | awk 'NR==2 {print $4}')"
if (( free_bytes < required_bytes )); then
  echo "QAZ.FUND preflight capacity gate failed: free=$free_bytes required=$required_bytes." >&2
  echo "Remote source, images, databases, and unrelated products were not changed." >&2
  exit 73
fi
printf 'QAZ.FUND preflight capacity gate passed: free=%s required=%s.\n' \
  "$free_bytes" "$required_bytes"
QAZ_FUND_CAPACITY_PREFLIGHT
}

run_remote_capacity_preflight

# Build the transport tree from Git, not from the checkout.  This prevents
# ignored local files or residue from an older remote release entering the
# production Docker context while preserving operational state explicitly.
SOURCE_STAGE="$(mktemp -d "${TMPDIR:-/tmp}/qaz-fund-source.${REVISION:0:12}.XXXXXX")"
cleanup_source_stage() {
  rm -rf -- "$SOURCE_STAGE"
}
trap cleanup_source_stage EXIT
git archive "$REVISION" | tar -x -C "$SOURCE_STAGE"

SOURCE_BACKUP_DIR="$SOURCE_BACKUP_ROOT/$RELEASE_STAMP-${REVISION:0:12}"
printf -v source_backup_command 'install -d -m 700 %q' "$SOURCE_BACKUP_DIR"
ssh "$DEPLOY_HOST" "$source_backup_command"

RSYNC_ARGS=(
  -az
  --delete-delay
  --backup
  "--backup-dir=$SOURCE_BACKUP_DIR"
  --exclude ".env.prod*"
  --exclude ".release.env"
  --exclude ".deployed-revision"
  --exclude ".deployed-at"
  --exclude ".git"
  --exclude ".venv"
  --exclude "work"
  --exclude "data"
)

rsync "${RSYNC_ARGS[@]}" "$SOURCE_STAGE/" "$DEPLOY_HOST:$DEPLOY_PATH/"
echo "Exact source sync completed; replaced files retained in $SOURCE_BACKUP_DIR"

ssh "$DEPLOY_HOST" \
  "cd '$DEPLOY_PATH' && env \
    DEPLOY_PATH='$DEPLOY_PATH' \
    ENV_FILE='$ENV_FILE' \
    COMPOSE_FILES='$COMPOSE_FILES' \
    REVISION='$REVISION' \
    DEPLOYED_AT='$DEPLOYED_AT' \
    BUILT_AT='$BUILT_AT' \
    ARTIFACT_DIGEST='$ARTIFACT_DIGEST' \
    MIN_FREE_BYTES='$MIN_FREE_BYTES' \
    READY_URL='$READY_URL' \
    READY_ATTEMPTS='$READY_ATTEMPTS' \
    READY_DELAY='$READY_DELAY' \
    SEMANTIC_READY_ATTEMPTS='$SEMANTIC_READY_ATTEMPTS' \
    SEMANTIC_READY_DELAY='$SEMANTIC_READY_DELAY' \
    WORKER_READY_ATTEMPTS='$WORKER_READY_ATTEMPTS' \
    WORKER_READY_DELAY='$WORKER_READY_DELAY' \
    PUBLIC_URL='$PUBLIC_URL' \
    REQUIRE_PUBLIC_VERIFY='$REQUIRE_PUBLIC_VERIFY' \
    RECONCILE_SOURCE_DUMP='$RECONCILE_SOURCE_DUMP' \
    RECONCILE_SOURCE_DUMP_SHA256='$RECONCILE_SOURCE_DUMP_SHA256' \
    RECONCILE_EXPECTED_SOURCE_COUNT='$RECONCILE_EXPECTED_SOURCE_COUNT' \
    RECONCILE_EXPECTED_TARGET_COUNT='$RECONCILE_EXPECTED_TARGET_COUNT' \
    bash scripts/remote_release_qaz_fund.sh"

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
