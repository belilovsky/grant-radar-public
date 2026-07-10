from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_deploy_script_requires_explicit_delete_opt_in() -> None:
    script = (ROOT / "scripts" / "deploy_qaz_fund.sh").read_text()

    assert 'RSYNC_DELETE="${RSYNC_DELETE:-0}"' in script
    assert 'if [[ "$RSYNC_DELETE" == "1" ]]; then' in script
    assert "RSYNC_ARGS+=(--delete)" in script
    assert (
        'rsync "${RSYNC_ARGS[@]}" "$ROOT_DIR/" "$DEPLOY_HOST:$DEPLOY_PATH/"' in script
    )


def test_deploy_script_no_longer_uses_unconditional_delete() -> None:
    script = (ROOT / "scripts" / "deploy_qaz_fund.sh").read_text()

    assert "rsync -az --delete" not in script


def test_deploy_script_waits_for_ready_endpoint() -> None:
    script = (ROOT / "scripts" / "deploy_qaz_fund.sh").read_text()

    assert 'READY_URL="${READY_URL:-http://127.0.0.1:8000/ready}"' in script
    assert 'READY_ATTEMPTS="${READY_ATTEMPTS:-30}"' in script
    assert 'READY_DELAY="${READY_DELAY:-2}"' in script
    assert (
        "docker compose --env-file '$ENV_FILE' $COMPOSE_FILES exec -T api \\" in script
    )
    assert "curl -fsS '$READY_URL' >/dev/null" in script
    assert "API readiness check failed after deploy." in script


def test_production_compose_requires_password_and_checks_api_readiness() -> None:
    base_compose = (ROOT / "docker-compose.yml").read_text()
    production_compose = (ROOT / "docker-compose.prod.yml").read_text()

    assert "http://127.0.0.1:8000/ready" in base_compose
    assert "POSTGRES_PASSWORD must be set in .env.prod" in production_compose


def test_backup_script_creates_rotated_postgres_dumps() -> None:
    script = (ROOT / "scripts" / "backup_postgres.sh").read_text()

    assert "pg_dump" in script
    assert "--format=custom" in script
    assert "KEEP_DAYS" in script
    assert "qaz-fund-*.dump" in script
    assert 'rm -f "$temporary_path"' in script
