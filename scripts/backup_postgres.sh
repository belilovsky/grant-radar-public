#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$ROOT_DIR/backups}"
KEEP_DAYS="${KEEP_DAYS:-14}"
POSTGRES_USER="${POSTGRES_USER:-grantradar}"
POSTGRES_DB="${POSTGRES_DB:-grantradar}"
BACKUP_GPG_RECIPIENT="${BACKUP_GPG_RECIPIENT:-}"
ENV_FILE="${ENV_FILE:-.env.prod}"
COMPOSE_FILES="${COMPOSE_FILES:--f docker-compose.yml -f docker-compose.prod.yml}"

if ! [[ "$KEEP_DAYS" =~ ^[0-9]+$ ]]; then
  echo "KEEP_DAYS must be a non-negative integer." >&2
  exit 2
fi

cd "$ROOT_DIR"
install -d -m 700 "$BACKUP_DIR"

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
dump_path="$BACKUP_DIR/qaz-fund-$timestamp.dump"
temporary_path="$dump_path.partial"
encrypted_path="$dump_path.gpg"
encrypted_temporary_path="$encrypted_path.partial"

cleanup() {
  rm -f "$temporary_path" "$encrypted_temporary_path"
}
trap cleanup EXIT

docker compose --env-file "$ENV_FILE" $COMPOSE_FILES exec -T db \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom >"$temporary_path"

if [[ ! -s "$temporary_path" ]]; then
  echo "Database dump is empty." >&2
  exit 1
fi

chmod 600 "$temporary_path"
if command -v pg_restore >/dev/null 2>&1; then
  pg_restore --list "$temporary_path" >/dev/null
else
  docker compose --env-file "$ENV_FILE" $COMPOSE_FILES exec -T db \
    pg_restore --list <"$temporary_path" >/dev/null
fi
if [[ -n "$BACKUP_GPG_RECIPIENT" ]]; then
  if ! command -v gpg >/dev/null 2>&1; then
    echo "gpg is required when BACKUP_GPG_RECIPIENT is set." >&2
    exit 1
  fi
  gpg --batch --yes --trust-model always \
    --recipient "$BACKUP_GPG_RECIPIENT" \
    --output "$encrypted_temporary_path" \
    --encrypt "$temporary_path"
  chmod 600 "$encrypted_temporary_path"
  mv "$encrypted_temporary_path" "$encrypted_path"
  final_path="$encrypted_path"
  rm -f "$temporary_path"
else
  mv "$temporary_path" "$dump_path"
  final_path="$dump_path"
  echo "Warning: BACKUP_GPG_RECIPIENT is unset; archive is protected by mode 0600 only." >&2
fi

checksum_path="$final_path.sha256"
if command -v sha256sum >/dev/null 2>&1; then
  (
    cd "$BACKUP_DIR"
    sha256sum "$(basename "$final_path")" >"$(basename "$checksum_path")"
  )
elif command -v shasum >/dev/null 2>&1; then
  (
    cd "$BACKUP_DIR"
    shasum -a 256 "$(basename "$final_path")" >"$(basename "$checksum_path")"
  )
else
  echo "A SHA-256 utility is required to verify the backup." >&2
  exit 1
fi
chmod 600 "$checksum_path"

find "$BACKUP_DIR" -maxdepth 1 -type f \
  \( -name 'qaz-fund-*.dump' -o -name 'qaz-fund-*.dump.gpg' \) \
  -mtime "+$KEEP_DAYS" -delete
find "$BACKUP_DIR" -maxdepth 1 -type f -name 'qaz-fund-*.dump*.sha256' \
  -mtime "+$KEEP_DAYS" -delete

echo "Created $final_path and $checksum_path"
