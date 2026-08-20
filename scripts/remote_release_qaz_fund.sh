#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="${DEPLOY_PATH:-/opt/grant-radar}"
ENV_FILE="${ENV_FILE:-.env.prod}"
COMPOSE_FILES="${COMPOSE_FILES:--f docker-compose.yml -f docker-compose.prod.yml}"
REVISION="${REVISION:?REVISION is required}"
DEPLOYED_AT="${DEPLOYED_AT:?DEPLOYED_AT is required}"
BUILT_AT="${BUILT_AT:?BUILT_AT is required}"
ARTIFACT_DIGEST="${ARTIFACT_DIGEST:?ARTIFACT_DIGEST is required}"
MIN_FREE_BYTES="${MIN_FREE_BYTES:-21474836480}"
READY_URL="${READY_URL:-http://127.0.0.1:8000/ready}"
READY_ATTEMPTS="${READY_ATTEMPTS:-30}"
READY_DELAY="${READY_DELAY:-2}"
SEMANTIC_READY_ATTEMPTS="${SEMANTIC_READY_ATTEMPTS:-450}"
SEMANTIC_READY_DELAY="${SEMANTIC_READY_DELAY:-2}"
WORKER_READY_ATTEMPTS="${WORKER_READY_ATTEMPTS:-120}"
WORKER_READY_DELAY="${WORKER_READY_DELAY:-2}"
PUBLIC_URL="${PUBLIC_URL:-}"
REQUIRE_PUBLIC_VERIFY="${REQUIRE_PUBLIC_VERIFY:-1}"
RECONCILE_SOURCE_DUMP="${RECONCILE_SOURCE_DUMP:-}"
RECONCILE_SOURCE_DUMP_SHA256="${RECONCILE_SOURCE_DUMP_SHA256:-}"
RECONCILE_EXPECTED_SOURCE_COUNT="${RECONCILE_EXPECTED_SOURCE_COUNT:-}"
RECONCILE_EXPECTED_TARGET_COUNT="${RECONCILE_EXPECTED_TARGET_COUNT:-}"
INSTALL_NGINX_CONFIG="${INSTALL_NGINX_CONFIG:-1}"
RESTORE_DB_ON_ROLLBACK="${RESTORE_DB_ON_ROLLBACK:-1}"
LOCK_FILE="${LOCK_FILE:-/var/lock/qaz-fund-deploy.lock}"
BACKUP_ROOT="${BACKUP_ROOT:-/var/backups/grant-radar/releases}"

if ! [[ "$REVISION" =~ ^[0-9a-f]{40}$ ]]; then
  echo "REVISION must be a full lowercase Git SHA." >&2
  exit 2
fi
if ! [[ "$ARTIFACT_DIGEST" =~ ^sha256:[0-9a-f]{64}$ ]]; then
  echo "ARTIFACT_DIGEST must be a sha256 digest." >&2
  exit 2
fi
if [[ "$REQUIRE_PUBLIC_VERIFY" == "1" && -z "$PUBLIC_URL" ]]; then
  echo "PUBLIC_URL is required for public release acceptance." >&2
  exit 2
fi
if [[ -n "$RECONCILE_SOURCE_DUMP" ]]; then
  case "$RECONCILE_SOURCE_DUMP" in
    /var/backups/grant-radar/*) ;;
    *)
      echo "RECONCILE_SOURCE_DUMP must be inside /var/backups/grant-radar/." >&2
      exit 2
      ;;
  esac
  if [[ ! -s "$RECONCILE_SOURCE_DUMP" ]]; then
    echo "Reconciliation source dump is missing or empty." >&2
    exit 2
  fi
  if ! [[ "$RECONCILE_SOURCE_DUMP_SHA256" =~ ^[0-9a-f]{64}$ ]]; then
    echo "RECONCILE_SOURCE_DUMP_SHA256 must be an unprefixed SHA-256." >&2
    exit 2
  fi
  printf '%s  %s\n' "$RECONCILE_SOURCE_DUMP_SHA256" "$RECONCILE_SOURCE_DUMP" | sha256sum -c -
fi

cd "$ROOT_DIR"
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "Another QAZ.FUND release holds $LOCK_FILE." >&2
  exit 75
fi

compose() {
  docker compose --env-file "$ENV_FILE" --env-file .release.env \
    $COMPOSE_FILES "$@"
}

wait_for_api() {
  local ready_ok=0
  for _attempt in $(seq 1 "$READY_ATTEMPTS"); do
    if compose exec -T api curl -fsS "$READY_URL" >/dev/null 2>&1; then
      ready_ok=1
      break
    fi
    sleep "$READY_DELAY"
  done
  if [[ "$ready_ok" != "1" ]]; then
    echo "API readiness check failed after deploy." >&2
    compose logs --tail=80 api >&2 || true
    return 1
  fi
}

reconcile_database=""
cleanup_reconcile_database() {
  if [[ -n "$reconcile_database" ]]; then
    docker compose --env-file "$ENV_FILE" $COMPOSE_FILES exec -T db \
      dropdb --if-exists -U "${POSTGRES_USER:-grantradar}" \
      "$reconcile_database" >/dev/null 2>&1 || true
    reconcile_database=""
  fi
}

reconcile_from_dump() {
  if [[ -z "$RECONCILE_SOURCE_DUMP" ]]; then
    return
  fi
  reconcile_database="qazfund_reconcile_${REVISION:0:12}"
  docker compose --env-file "$ENV_FILE" $COMPOSE_FILES exec -T db \
    dropdb --if-exists -U "${POSTGRES_USER:-grantradar}" "$reconcile_database"
  docker compose --env-file "$ENV_FILE" $COMPOSE_FILES exec -T db \
    createdb -U "${POSTGRES_USER:-grantradar}" "$reconcile_database"
  docker compose --env-file "$ENV_FILE" $COMPOSE_FILES exec -T db \
    pg_restore --exit-on-error --no-owner \
    -U "${POSTGRES_USER:-grantradar}" -d "$reconcile_database" \
    <"$RECONCILE_SOURCE_DUMP"

  compose exec -T \
    -e RECONCILE_SOURCE_DATABASE="$reconcile_database" \
    -e RECONCILE_EXPECTED_SOURCE_COUNT="$RECONCILE_EXPECTED_SOURCE_COUNT" \
    -e RECONCILE_EXPECTED_TARGET_COUNT="$RECONCILE_EXPECTED_TARGET_COUNT" \
    api python - >"$backup_dir/reconciliation.json" <<'PY'
import json
import os
import sys

from sqlalchemy.engine import make_url

from scripts.reconcile_databases import reconcile

target_url = os.environ["GRANT_RADAR_DB_URL"]
source_url = make_url(target_url).set(
    database=os.environ["RECONCILE_SOURCE_DATABASE"]
).render_as_string(hide_password=False)
source_count_raw = os.environ.get("RECONCILE_EXPECTED_SOURCE_COUNT", "").strip()
target_count_raw = os.environ.get("RECONCILE_EXPECTED_TARGET_COUNT", "").strip()
source_count = int(source_count_raw) if source_count_raw else None
target_count = int(target_count_raw) if target_count_raw else None

dry_run = reconcile(
    source_url=source_url,
    target_url=target_url,
    expected_source_count=source_count,
    expected_target_count=target_count,
)
applied = reconcile(
    source_url=source_url,
    target_url=target_url,
    apply=True,
    expected_source_count=source_count,
    expected_target_count=target_count,
)
repeated = reconcile(source_url=source_url, target_url=target_url, apply=True)
mutation_keys = (
    "source_only_archived",
    "common_source_selected",
    "versions_added",
    "observations_added",
    "runs_added",
)
if dry_run["target_after"]["hash"] != applied["target_after"]["hash"]:
    raise RuntimeError("reconciliation dry-run and apply hashes differ")
if applied["target_after"]["hash"] != repeated["target_after"]["hash"]:
    raise RuntimeError("reconciliation changed its target hash on repeat")
if any(int(repeated["stats"][key]) for key in mutation_keys):
    raise RuntimeError("reconciliation is not idempotent")
json.dump(
    {"dry_run": dry_run, "applied": applied, "idempotence": repeated},
    sys.stdout,
    ensure_ascii=False,
    indent=2,
)
sys.stdout.write("\n")
PY
  cat "$backup_dir/reconciliation.json"
  cleanup_reconcile_database
}

current_api_image="$(docker compose --env-file "$ENV_FILE" $COMPOSE_FILES images -q api 2>/dev/null | head -n 1)"
current_semantic_image="$(docker compose --env-file "$ENV_FILE" $COMPOSE_FILES images -q semantic 2>/dev/null | head -n 1)"
current_revision="$(tr -d '[:space:]' <.deployed-revision 2>/dev/null || true)"
current_deployed_at="$(tr -d '[:space:]' <.deployed-at 2>/dev/null || true)"
if [[ -z "$current_api_image" || -z "$current_semantic_image" ]]; then
  echo "QAZ.FUND rollback gate failed: current API and semantic images are required." >&2
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
# Until the candidate is built, the current immutable pair is the conservative
# estimate.  Keep room for both candidate and rollback, with a 2x safety margin.
required_bytes="$(( 2 * (current_bytes + current_bytes) ))"
if (( required_bytes < MIN_FREE_BYTES )); then
  required_bytes="$MIN_FREE_BYTES"
fi
free_bytes="$(df -PB1 "$ROOT_DIR" | awk 'NR==2 {print $4}')"
if (( free_bytes < required_bytes )); then
  echo "QAZ.FUND capacity gate failed: free=$free_bytes required=$required_bytes." >&2
  echo "No image, database, volume, or unrelated product was deleted." >&2
  exit 73
fi

release_stamp="${DEPLOYED_AT//[:\-]/}"
release_stamp="${release_stamp//T/_}"
release_stamp="${release_stamp//Z/}"
backup_dir="$BACKUP_ROOT/$release_stamp"
install -d -m 700 "$backup_dir"

backup_marker="$(mktemp "$backup_dir/.before-backup.XXXXXX")"
BACKUP_DIR="$backup_dir" ENV_FILE="$ENV_FILE" COMPOSE_FILES="$COMPOSE_FILES" \
  scripts/backup_postgres.sh
db_snapshot="$(find "$backup_dir" -maxdepth 1 -type f -name 'qaz-fund-*.dump' -newer "$backup_marker" | sort | tail -n 1)"
rm -f "$backup_marker"
if [[ -z "$db_snapshot" || ! -s "$db_snapshot" ]]; then
  echo "Pre-release database snapshot was not created." >&2
  exit 1
fi

release_env_backup="$backup_dir/release.env.before"
release_env_existed=0
if [[ -f .release.env ]]; then
  cp --preserve=mode,timestamps .release.env "$release_env_backup"
  release_env_existed=1
fi
nginx_backup="$backup_dir/qaz.fund.conf.before"
if [[ -f /etc/nginx/sites-enabled/qaz.fund.conf ]]; then
  cp --preserve=mode,timestamps /etc/nginx/sites-enabled/qaz.fund.conf "$nginx_backup"
fi

if [[ -n "$current_api_image" && -n "$current_revision" ]]; then
  docker image tag "$current_api_image" "qaz-fund:rollback-$current_revision"
fi
if [[ -n "$current_semantic_image" && -n "$current_revision" ]]; then
  docker image tag "$current_semantic_image" "qaz-fund-semantic:rollback-$current_revision"
fi

release_env_changed=0
switched=0
rollback() {
  local exit_code=$?
  trap - ERR
  set +e
  if [[ "$switched" == "1" ]]; then
    echo "Release failed after switch; restoring the scoped QAZ.FUND rollback." >&2
    docker compose --env-file "$ENV_FILE" $COMPOSE_FILES stop api worker >/dev/null 2>&1
    if [[ "$RESTORE_DB_ON_ROLLBACK" == "1" && -s "$db_snapshot" ]]; then
      docker compose --env-file "$ENV_FILE" $COMPOSE_FILES exec -T db \
        pg_restore --clean --if-exists --no-owner \
        -U "${POSTGRES_USER:-grantradar}" -d "${POSTGRES_DB:-grantradar}" \
        <"$db_snapshot"
    fi
  fi
  if [[ "$release_env_changed" == "1" ]]; then
    if [[ "$release_env_existed" == "1" && -s "$release_env_backup" ]]; then
      install -m 600 "$release_env_backup" .release.env
    else
      printf '%s\n' \
        "APP_REVISION=${current_revision:-development}" \
        "APP_SOURCE_DIRTY=true" \
        "APP_IMAGE_DIGEST=$current_api_image" \
        "APP_ARTIFACT_DIGEST=" \
        "APP_BUILT_AT=" \
        "APP_DEPLOYED_AT=$current_deployed_at" \
        "QAZ_FUND_IMAGE=$current_api_image" \
        "QAZ_FUND_SEMANTIC_IMAGE=$current_semantic_image" \
        >.release.env
      chmod 600 .release.env
    fi
  fi
  if [[ "$switched" == "1" ]]; then
    export QAZ_FUND_IMAGE="$current_api_image"
    export QAZ_FUND_SEMANTIC_IMAGE="$current_semantic_image"
    export APP_REVISION="${current_revision:-development}"
    export APP_DEPLOYED_AT="$current_deployed_at"
    docker compose --env-file "$ENV_FILE" --env-file .release.env \
      $COMPOSE_FILES up -d --no-build api worker semantic
    if [[ -s "$nginx_backup" ]]; then
      install -m 644 "$nginx_backup" /etc/nginx/sites-available/qaz.fund.conf
      ln -sfn /etc/nginx/sites-available/qaz.fund.conf \
        /etc/nginx/sites-enabled/qaz.fund.conf
      nginx -t && systemctl reload nginx
    fi
  fi
  cleanup_reconcile_database
  echo "Rollback evidence is retained in $backup_dir." >&2
  exit "$exit_code"
}
trap rollback ERR

export APP_REVISION="$REVISION"
export QAZ_FUND_IMAGE="qaz-fund:$REVISION"
export QAZ_FUND_SEMANTIC_IMAGE="qaz-fund-semantic:$REVISION"
docker compose --env-file "$ENV_FILE" $COMPOSE_FILES build api semantic

api_image_digest="$(docker image inspect --format '{{.Id}}' "$QAZ_FUND_IMAGE")"
semantic_image_digest="$(docker image inspect --format '{{.Id}}' "$QAZ_FUND_SEMANTIC_IMAGE")"
if ! [[ "$api_image_digest" =~ ^sha256:[0-9a-f]{64}$ ]]; then
  echo "Built API image has no immutable SHA-256 identity." >&2
  exit 1
fi
if ! [[ "$semantic_image_digest" =~ ^sha256:[0-9a-f]{64}$ ]]; then
  echo "Built semantic image has no immutable SHA-256 identity." >&2
  exit 1
fi

release_env_tmp="$(mktemp .release.env.XXXXXX)"
printf '%s\n' \
  "APP_REVISION=$REVISION" \
  "APP_SOURCE_DIRTY=false" \
  "APP_IMAGE_DIGEST=$api_image_digest" \
  "APP_ARTIFACT_DIGEST=$ARTIFACT_DIGEST" \
  "APP_BUILT_AT=$BUILT_AT" \
  "APP_DEPLOYED_AT=$DEPLOYED_AT" \
  "QAZ_FUND_IMAGE=$QAZ_FUND_IMAGE" \
  "QAZ_FUND_SEMANTIC_IMAGE=$QAZ_FUND_SEMANTIC_IMAGE" \
  "QAZ_FUND_SEMANTIC_IMAGE_DIGEST=$semantic_image_digest" \
  >"$release_env_tmp"
chmod 600 "$release_env_tmp"
mv "$release_env_tmp" .release.env
release_env_changed=1

switched=1
compose up -d --no-build db qdrant api semantic
wait_for_api

reconcile_from_dump
if [[ -n "$RECONCILE_SOURCE_DUMP" ]]; then
  compose restart api semantic
  wait_for_api
fi

compose up -d --no-build worker

semantic_ok=0
for _attempt in $(seq 1 "$SEMANTIC_READY_ATTEMPTS"); do
  if compose exec -T semantic python -c \
    "from urllib.request import urlopen; urlopen('http://127.0.0.1:8010/health', timeout=3).read()" \
    >/dev/null 2>&1; then
    semantic_ok=1
    break
  fi
  sleep "$SEMANTIC_READY_DELAY"
done
if [[ "$semantic_ok" != "1" ]]; then
  echo "Semantic search did not become ready after deploy." >&2
  compose logs --tail=80 semantic >&2 || true
  false
fi

worker_ok=0
for _attempt in $(seq 1 "$WORKER_READY_ATTEMPTS"); do
  if compose exec -T worker python -c \
    "import os,time; path=os.environ['GRANT_RADAR_WORKER_HEARTBEAT_PATH']; age=time.time()-os.path.getmtime(path); raise SystemExit(0 if age < 120 else 1)" \
    >/dev/null 2>&1; then
    worker_ok=1
    break
  fi
  sleep "$WORKER_READY_DELAY"
done
if [[ "$worker_ok" != "1" ]]; then
  echo "Worker heartbeat did not become ready after deploy." >&2
  compose logs --tail=80 worker >&2 || true
  false
fi

if [[ "$INSTALL_NGINX_CONFIG" == "1" ]]; then
  install -m 644 deploy/nginx/qaz.fund.conf /etc/nginx/sites-available/qaz.fund.conf
  ln -sfn /etc/nginx/sites-available/qaz.fund.conf \
    /etc/nginx/sites-enabled/qaz.fund.conf
  nginx -t
  systemctl reload nginx
fi

if [[ "$REQUIRE_PUBLIC_VERIFY" == "1" ]]; then
  compose exec -T api python -m scripts.production_smoke \
    --base-url "$PUBLIC_URL" \
    --expect-backend database
fi

printf '%s\n' "$REVISION" >.deployed-revision
printf '%s\n' "$DEPLOYED_AT" >.deployed-at
compose ps
switched=0
trap - ERR
echo "Released QAZ.FUND $REVISION; rollback evidence: $backup_dir"
