#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST_DIR="${1:-${DEST_DIR:-$ROOT_DIR/../grant-radar-public}}"
FORCE_OVERWRITE="${FORCE_OVERWRITE:-0}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

DEST_DIR="$($PYTHON_BIN -c 'import os, sys; print(os.path.abspath(os.path.expanduser(sys.argv[1])))' "$DEST_DIR")"

if [[ "$DEST_DIR" == "/" || "$DEST_DIR" == "$ROOT_DIR" || "$DEST_DIR" == "$ROOT_DIR"/* ]]; then
  echo "Refusing unsafe export destination: $DEST_DIR" >&2
  exit 2
fi

if [[ -e "$DEST_DIR" && "$FORCE_OVERWRITE" != "1" ]]; then
  echo "Destination already exists: $DEST_DIR" >&2
  echo "Re-run with FORCE_OVERWRITE=1 to replace it." >&2
  exit 2
fi

rm -rf -- "$DEST_DIR"
mkdir -p "$DEST_DIR"

rsync -a \
  --exclude ".git" \
  --exclude ".github/workflows/*.local.*" \
  --exclude ".venv" \
  --exclude "__pycache__" \
  --exclude ".pytest_cache" \
  --exclude ".mypy_cache" \
  --exclude ".ruff_cache" \
  --exclude ".cache" \
  --exclude ".mcp.json" \
  --exclude ".env" \
  --exclude ".env.dev" \
  --exclude ".env.staging" \
  --exclude ".env.prod" \
  --exclude "data/*.db" \
  --exclude "data/*.sqlite" \
  --exclude "data/*.sqlite3" \
  --exclude "data/*.db-journal" \
  --exclude "CONTEXT.md" \
  "$ROOT_DIR/" "$DEST_DIR/"

git -C "$DEST_DIR" init -b main >/dev/null
git -C "$DEST_DIR" config user.name "${EXPORT_GIT_AUTHOR_NAME:-QAZ.FUND exporter}"
git -C "$DEST_DIR" config user.email "${EXPORT_GIT_AUTHOR_EMAIL:-export@qaz.fund}"
git -C "$DEST_DIR" add .
git -C "$DEST_DIR" commit -m "Initial public release" >/dev/null

echo "Public repository snapshot created at: $DEST_DIR"
