from __future__ import annotations

import os
import subprocess
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
    assert "curl -fsS '$READY_URL' >/dev/null 2>&1" in script
    assert "API readiness check failed after deploy." in script


def test_deploy_script_verifies_the_public_revision() -> None:
    script = (ROOT / "scripts" / "deploy_qaz_fund.sh").read_text()
    production_compose = (ROOT / "docker-compose.prod.yml").read_text()

    assert 'REQUIRE_PUBLIC_VERIFY="${REQUIRE_PUBLIC_VERIFY:-1}"' in script
    assert 'PUBLIC_URL="${PUBLIC_URL:-}"' in script
    assert "/.well-known/release.json?revision=$REVISION" in script
    assert 'if [[ "$public_revision" != "$REVISION" ]]; then' in script
    assert "APP_REVISION: ${APP_REVISION:-development}" in production_compose
    assert "APP_DEPLOYED_AT: ${APP_DEPLOYED_AT:-}" in production_compose


def test_production_compose_requires_password_and_checks_api_readiness() -> None:
    base_compose = (ROOT / "docker-compose.yml").read_text()
    production_compose = (ROOT / "docker-compose.prod.yml").read_text()

    assert "http://127.0.0.1:8000/ready" in base_compose
    assert "POSTGRES_PASSWORD must be set in .env.prod" in production_compose
    assert "  db:\n    env_file:" not in production_compose


def test_worker_does_not_run_migrations_concurrently_with_api() -> None:
    base_compose = (ROOT / "docker-compose.yml").read_text()

    assert 'GRANT_RADAR_SKIP_MIGRATIONS: "1"' in base_compose


def test_backup_script_creates_rotated_postgres_dumps() -> None:
    script = (ROOT / "scripts" / "backup_postgres.sh").read_text()

    assert "pg_dump" in script
    assert "--format=custom" in script
    assert "KEEP_DAYS" in script
    assert "qaz-fund-*.dump" in script
    assert 'rm -f "$temporary_path"' in script


def test_public_export_rejects_destructive_destination_paths() -> None:
    script = (ROOT / "scripts" / "export_public_repo.sh").read_text()

    assert 'DEST_DIR="$($PYTHON_BIN -c' in script
    assert 'if [[ "$DEST_DIR" == "/"' in script
    assert '|| "$DEST_DIR" == "$ROOT_DIR"/*' in script
    assert 'rm -rf -- "$DEST_DIR"' in script
    assert '--exclude "docs/cleanup"' not in script


def test_public_export_accepts_destination_from_environment(tmp_path: Path) -> None:
    destination = tmp_path / "public-export"
    environment = {
        **os.environ,
        "DEST_DIR": str(destination),
        "FORCE_OVERWRITE": "1",
    }

    result = subprocess.run(
        ["bash", str(ROOT / "scripts" / "export_public_repo.sh")],
        cwd=ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert (destination / ".git").is_dir()
    assert (destination / "docs" / "cleanup" / "README.md").is_file()
