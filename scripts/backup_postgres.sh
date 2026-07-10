#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$ROOT_DIR/backups}"
KEEP_DAYS="${KEEP_DAYS:-14}"
POSTGRES_USER="${POSTGRES_USER:-grantradar}"
POSTGRES_DB="${POSTGRES_DB:-grantradar}"

if ! [[ "$KEEP_DAYS" =~ ^[0-9]+$ ]]; then
  echo "KEEP_DAYS must be a non-negative integer." >&2
  exit 2
fi

cd "$ROOT_DIR"
install -d -m 700 "$BACKUP_DIR"

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
final_path="$BACKUP_DIR/qaz-fund-$timestamp.dump"
temporary_path="$final_path.partial"

cleanup() {
  rm -f "$temporary_path"
}
trap cleanup EXIT

docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T db \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom >"$temporary_path"

if [[ ! -s "$temporary_path" ]]; then
  echo "Database dump is empty." >&2
  exit 1
fi

chmod 600 "$temporary_path"
mv "$temporary_path" "$final_path"
find "$BACKUP_DIR" -maxdepth 1 -type f -name 'qaz-fund-*.dump' -mtime "+$KEEP_DAYS" -delete

echo "Created $final_path"
