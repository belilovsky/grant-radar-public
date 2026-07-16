from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_dev_requirements_reuse_runtime_requirements():
    requirements = (ROOT / "requirements.txt").read_text()
    dockerfile = (ROOT / "Dockerfile").read_text()

    assert "-r requirements-prod.txt" in requirements
    assert "COPY requirements.txt requirements-prod.txt ./" in dockerfile


def test_prod_image_uses_runtime_requirements():
    dockerfile = (ROOT / "Dockerfile.prod").read_text()

    assert "requirements-prod.txt" in dockerfile
    assert "requirements.txt" not in dockerfile
    assert "build-essential" not in dockerfile


def test_prod_requirements_exclude_dev_and_browser_tooling():
    requirements = (ROOT / "requirements-prod.txt").read_text()
    excluded = (
        "black",
        "flake8",
        "isort",
        "mypy",
        "playwright",
        "pre-commit",
        "pytest",
        "respx",
        "ruff",
    )

    for package in excluded:
        assert f"{package}==" not in requirements


def test_qazstack_runtime_dependencies_are_pinned():
    requirements = (ROOT / "requirements-prod.txt").read_text()

    for package in ("asyncpg", "jinja2", "python-multipart"):
        assert f"{package}==" in requirements


def test_runtime_requirements_exclude_removed_integrations():
    requirements = (ROOT / "requirements-prod.txt").read_text()
    removed = (
        "apscheduler",
        "celery",
        "google-api-python-client",
        "google-auth",
        "python-telegram-bot",
        "redis",
        "tenacity",
    )

    for package in removed:
        assert f"{package}==" not in requirements


def test_runtime_requirements_declare_direct_tls_dependency():
    requirements = (ROOT / "requirements-prod.txt").read_text()

    assert "certifi==" in requirements


def test_dev_requirements_use_current_browser_and_test_client_tooling():
    requirements = (ROOT / "requirements.txt").read_text()

    assert "httpx2==2.7.0" in requirements
    assert "playwright==1.61.0" in requirements
    assert "vulture==2.16" in requirements
    assert "ruff==" not in requirements


def test_compose_does_not_require_the_removed_redis_runtime():
    compose_files = (
        ROOT / "docker-compose.yml",
        ROOT / "docker-compose.dev.yml",
        ROOT / "docker-compose.staging.yml",
        ROOT / "docker-compose.prod.yml",
    )

    for path in compose_files:
        compose = path.read_text()
        assert "REDIS_URL" not in compose
        assert "  redis:" not in compose
