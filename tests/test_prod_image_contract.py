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
