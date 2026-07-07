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
