#!/usr/bin/env sh
# Production entrypoint: run pending Alembic migrations, then exec the app.
#
# Skips migrations when GRANT_RADAR_SKIP_MIGRATIONS=1 (useful for one-off jobs
# or environments where the schema is managed externally).
set -eu

MIGRATION_ATTEMPTS="${GRANT_RADAR_MIGRATION_ATTEMPTS:-30}"
MIGRATION_SLEEP_SECONDS="${GRANT_RADAR_MIGRATION_SLEEP_SECONDS:-2}"

if [ "${GRANT_RADAR_SKIP_MIGRATIONS:-0}" != "1" ]; then
  attempt=1
  while :; do
    echo "[entrypoint] running alembic upgrade head (attempt ${attempt}/${MIGRATION_ATTEMPTS})..."
    if alembic upgrade head; then
      break
    fi
    if [ "$attempt" -ge "$MIGRATION_ATTEMPTS" ]; then
      echo "[entrypoint] alembic upgrade failed after ${MIGRATION_ATTEMPTS} attempts" >&2
      exit 1
    fi
    attempt=$((attempt + 1))
    sleep "$MIGRATION_SLEEP_SECONDS"
  done
else
  echo "[entrypoint] GRANT_RADAR_SKIP_MIGRATIONS=1, skipping migrations"
fi

echo "[entrypoint] starting: $*"
exec "$@"
