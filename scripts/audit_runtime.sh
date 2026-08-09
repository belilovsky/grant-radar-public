#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-.env.prod}"
COMPOSE_FILES="${COMPOSE_FILES:--f docker-compose.yml -f docker-compose.prod.yml}"
PROJECT_PATTERN="${PROJECT_PATTERN:-grant-radar|qaz[.-]?fund|core[.]scheduler}"

cd "$ROOT_DIR"

echo "QAZ.FUND runtime audit"
echo "working_directory=$ROOT_DIR"

if command -v git >/dev/null 2>&1; then
  echo "revision=$(git rev-parse HEAD 2>/dev/null || echo unavailable)"
fi

if command -v docker >/dev/null 2>&1 && [[ -f "$ENV_FILE" ]]; then
  echo "compose_services"
  # The env file is read by Compose but its values are never printed.
  docker compose --env-file "$ENV_FILE" $COMPOSE_FILES ps
  echo "matching_containers"
  docker ps --format '{{.ID}} {{.Names}} {{.Status}} {{.Ports}}' |
    grep -Ei "$PROJECT_PATTERN" || true
else
  echo "compose_services=unavailable"
fi

echo "matching_processes"
ps -eo pid=,ppid=,lstart=,command= |
  grep -Ei "$PROJECT_PATTERN" |
  grep -Ev 'grep -E|audit_runtime[.]sh' || true

echo "matching_user_cron"
if command -v crontab >/dev/null 2>&1; then
  crontab -l 2>/dev/null | grep -Ei "$PROJECT_PATTERN" || true
else
  echo "crontab=unavailable"
fi

echo "matching_systemd_units"
if command -v systemctl >/dev/null 2>&1; then
  systemctl list-unit-files --type=service --type=timer --no-legend 2>/dev/null |
    grep -Ei "$PROJECT_PATTERN" || true
  systemctl list-timers --all --no-legend 2>/dev/null |
    grep -Ei "$PROJECT_PATTERN" || true
else
  echo "systemd=unavailable"
fi

echo "listening_ports"
if command -v ss >/dev/null 2>&1; then
  ss -lntp 2>/dev/null |
    grep -E '(:5432|:8000|:80 |:443 )' || true
elif command -v lsof >/dev/null 2>&1; then
  lsof -nP -iTCP -sTCP:LISTEN |
    grep -E '(:5432|:8000|:80 |:443 )' || true
else
  echo "port_inspection=unavailable"
fi
