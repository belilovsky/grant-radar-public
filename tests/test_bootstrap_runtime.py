from __future__ import annotations

from types import SimpleNamespace

from scripts import check_python_version


def test_check_python_version_accepts_supported_runtime(monkeypatch) -> None:
    fake_sys = SimpleNamespace(version_info=(3, 12, 1), stderr=None)
    monkeypatch.setattr(check_python_version, "sys", fake_sys)

    assert check_python_version.main() == 0


def test_check_python_version_rejects_older_runtime(monkeypatch) -> None:
    messages: list[str] = []
    fake_sys = SimpleNamespace(
        version_info=(3, 9, 6),
        stderr=SimpleNamespace(write=messages.append),
    )
    monkeypatch.setattr(check_python_version, "sys", fake_sys)

    assert check_python_version.main() == 2
    assert messages
    assert "requires Python 3.12+" in messages[0]
    assert "found 3.9.6" in messages[0]
