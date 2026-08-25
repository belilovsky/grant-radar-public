from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_deploy_script_syncs_an_exact_git_archive_and_preserves_runtime_state() -> None:
    script = (ROOT / "scripts" / "deploy_qaz_fund.sh").read_text()

    assert 'git archive "$REVISION" | tar -x -C "$SOURCE_STAGE"' in script
    assert "--delete-delay" in script
    assert "--backup" in script
    assert '"--backup-dir=$SOURCE_BACKUP_DIR"' in script
    assert (
        'rsync "${RSYNC_ARGS[@]}" "$SOURCE_STAGE/" "$DEPLOY_HOST:$DEPLOY_PATH/"'
        in script
    )
    assert '--exclude ".env.prod*"' in script
    assert '--exclude ".release.env"' in script
    assert '--exclude "work"' in script
    assert '--exclude "data"' in script


def test_deploy_script_checks_capacity_before_remote_source_changes() -> None:
    script = (ROOT / "scripts" / "deploy_qaz_fund.sh").read_text()

    preflight = script.index("run_remote_capacity_preflight\n")
    rsync = script.index(
        'rsync "${RSYNC_ARGS[@]}" "$SOURCE_STAGE/" "$DEPLOY_HOST:$DEPLOY_PATH/"'
    )
    assert preflight < rsync
    assert "QAZ.FUND preflight capacity gate failed" in script
    assert (
        "Remote source, images, databases, and unrelated products were not changed."
        in script
    )


def test_deploy_script_backs_up_replaced_source_before_exact_sync() -> None:
    script = (ROOT / "scripts" / "deploy_qaz_fund.sh").read_text()

    backup_dir = script.index('ssh "$DEPLOY_HOST" "$source_backup_command"')
    rsync = script.index(
        'rsync "${RSYNC_ARGS[@]}" "$SOURCE_STAGE/" "$DEPLOY_HOST:$DEPLOY_PATH/"'
    )
    assert backup_dir < rsync
    assert "Exact source sync completed; replaced files retained" in script


def test_production_context_excludes_runtime_and_browser_artifacts() -> None:
    dockerignore = (ROOT / ".dockerignore").read_text().splitlines()

    for path in (
        ".release.env",
        ".deployed-revision",
        ".deployed-at",
        "data/",
        "work/",
        "output/",
        ".playwright-cli/",
        ".qazfund-release-staging/",
    ):
        assert path in dockerignore


def test_browser_ci_uses_the_prebuilt_browser_runner_without_root_escalation() -> None:
    workflow = (ROOT / ".github" / "workflows" / "verify.yml").read_text()

    assert "runs-on: [self-hosted, Linux, X64, qdev-ci-browser" in workflow
    assert "actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020" in workflow
    assert 'node-version: "22"' in workflow
    assert "python -m playwright install chromium" in workflow
    assert "playwright install --with-deps" not in workflow


def test_runner_smoke_has_qdev_concurrency_and_cancellation() -> None:
    workflow = (ROOT / ".github" / "workflows" / "runner-smoke.yml").read_text()

    assert "group: runner-smoke-${{ github.workflow }}-${{ github.ref }}" in workflow
    assert "cancel-in-progress: true" in workflow


def test_deploy_script_waits_for_ready_endpoint() -> None:
    script = (ROOT / "scripts" / "deploy_qaz_fund.sh").read_text()
    remote = (ROOT / "scripts" / "remote_release_qaz_fund.sh").read_text()

    assert 'READY_URL="${READY_URL:-http://127.0.0.1:8000/ready}"' in script
    assert 'READY_ATTEMPTS="${READY_ATTEMPTS:-30}"' in script
    assert 'READY_DELAY="${READY_DELAY:-2}"' in script
    assert 'compose exec -T api curl -fsS "$READY_URL"' in remote
    assert "API readiness check failed after deploy." in remote
    assert "Semantic search did not become ready after deploy." in remote
    assert "Worker heartbeat did not become ready after deploy." in remote


def test_remote_release_has_capacity_backup_lock_identity_and_rollback_gates() -> None:
    remote = (ROOT / "scripts" / "remote_release_qaz_fund.sh").read_text()

    assert 'MIN_FREE_BYTES="${MIN_FREE_BYTES:-21474836480}"' in remote
    assert "2 * (current_bytes + current_bytes)" in remote
    assert "flock -n 9" in remote
    assert "QAZ.FUND rollback gate failed" in remote
    assert "scripts/backup_postgres.sh" in remote
    assert "APP_SOURCE_DIRTY=false" in remote
    assert "APP_IMAGE_DIGEST=$api_image_digest" in remote
    assert "pg_restore --clean --if-exists --no-owner" in remote
    assert "deploy/nginx/qaz.fund.conf" in remote
    assert "reconcile_from_dump" in remote
    assert "reconciliation.json" in remote
    assert "reconciliation is not idempotent" in remote
    assert "ensure_semantic_volume_owner" in remote
    assert '"$semantic_volume:/models"' in remote
    assert "chown -R 10001:10001 /models" in remote


def test_deploy_script_verifies_the_public_revision() -> None:
    script = (ROOT / "scripts" / "deploy_qaz_fund.sh").read_text()
    production_compose = (ROOT / "docker-compose.prod.yml").read_text()

    assert 'REQUIRE_PUBLIC_VERIFY="${REQUIRE_PUBLIC_VERIFY:-1}"' in script
    assert 'PUBLIC_URL="${PUBLIC_URL:-}"' in script
    assert "/.well-known/release.json?revision=$REVISION" in script
    assert 'if [[ "$public_revision" != "$REVISION" ]]; then' in script
    assert "APP_REVISION: ${APP_REVISION:-development}" in production_compose
    assert "APP_DEPLOYED_AT: ${APP_DEPLOYED_AT:-}" in production_compose


def test_production_compose_defaults_to_the_canonical_public_origin() -> None:
    production_compose = (ROOT / "docker-compose.prod.yml").read_text()

    assert production_compose.count("${PUBLIC_BASE_URL:-https://qaz.fund}") == 2
    assert (
        "PUBLIC_BASE_URL: ${PUBLIC_BASE_URL:-https://example.org}"
        not in production_compose
    )


def test_remote_release_runs_public_smoke_before_accepting_switch() -> None:
    remote = (ROOT / "scripts" / "remote_release_qaz_fund.sh").read_text()

    smoke = remote.index("python -m scripts.production_smoke")
    accepted = remote.index("switched=0\ntrap - ERR")
    assert smoke < accepted
    assert "--expect-backend database" in remote


def test_production_compose_requires_password_and_checks_api_readiness() -> None:
    base_compose = (ROOT / "docker-compose.yml").read_text()
    production_compose = (ROOT / "docker-compose.prod.yml").read_text()

    assert "http://127.0.0.1:8000/ready" in base_compose
    assert "POSTGRES_PASSWORD must be set in .env.prod" in production_compose
    assert "  db:\n    env_file:" not in production_compose


def test_semantic_catalog_uses_the_public_host_on_the_internal_network() -> None:
    production_compose = (ROOT / "docker-compose.prod.yml").read_text()

    assert "GRANT_RADAR_SEMANTIC_CATALOG_HOST" in production_compose
    assert "${GRANT_RADAR_SEMANTIC_CATALOG_HOST:-qaz.fund}" in production_compose
    assert "${GRANT_RADAR_SEMANTIC_CATALOG_TIMEOUT_SECONDS:-90}" in production_compose
    assert "${GRANT_RADAR_SEMANTIC_TIMEOUT_SECONDS:-15}" in production_compose
    assert "${GRANT_RADAR_SEMANTIC_RERANK_LIMIT:-5}" in production_compose
    assert "${GRANT_RADAR_SEMANTIC_RERANK_MAX_LENGTH:-256}" in production_compose


def test_semantic_runtime_is_reaped_and_bounded() -> None:
    production_compose = (ROOT / "docker-compose.prod.yml").read_text()
    semantic = production_compose.split("\n  semantic:\n", maxsplit=1)[1]

    assert "    init: true\n" in semantic
    assert '        "--workers",\n        "1",' in semantic
    assert '    cpus: "1.0"\n' in semantic
    assert "    mem_limit: 5g\n" in semantic
    assert "    pids_limit: 128\n" in semantic


def test_worker_does_not_run_migrations_concurrently_with_api() -> None:
    base_compose = (ROOT / "docker-compose.yml").read_text()

    assert 'GRANT_RADAR_SKIP_MIGRATIONS: "1"' in base_compose


def test_production_runtime_has_web_redundancy_and_worker_liveness() -> None:
    base_compose = (ROOT / "docker-compose.yml").read_text()
    production_compose = (ROOT / "docker-compose.prod.yml").read_text()

    assert "WEB_CONCURRENCY: ${WEB_CONCURRENCY:-1}" in production_compose
    assert "GRANT_RADAR_MAX_SOURCE_CONCURRENCY" in base_compose
    assert (
        "GRANT_RADAR_TIME_ZONE: ${GRANT_RADAR_TIME_ZONE:-Asia/Almaty}" in base_compose
    )
    assert "TZ: ${GRANT_RADAR_TIME_ZONE:-Asia/Almaty}" in base_compose
    assert "GRANT_RADAR_WORKER_HEARTBEAT_PATH" in base_compose
    assert "age < 120" in base_compose
    assert "start_period: 90s" in base_compose


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
        "GIT_CONFIG_GLOBAL": os.devnull,
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
    author = subprocess.run(
        ["git", "-C", str(destination), "log", "-1", "--format=%an <%ae>"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert author.stdout.strip() == "QAZ.FUND exporter <export@qaz.fund>"
