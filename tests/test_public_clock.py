from datetime import date, datetime, timezone

from core.public_clock import PUBLIC_TIME_ZONE_ENV, public_time_zone_name, public_today


def test_public_today_rolls_over_at_almaty_midnight(monkeypatch):
    monkeypatch.delenv(PUBLIC_TIME_ZONE_ENV, raising=False)

    before_midnight = datetime(2026, 7, 27, 18, 59, tzinfo=timezone.utc)
    after_midnight = datetime(2026, 7, 27, 19, 0, tzinfo=timezone.utc)

    assert public_time_zone_name() == "Asia/Almaty"
    assert public_today(before_midnight) == date(2026, 7, 27)
    assert public_today(after_midnight) == date(2026, 7, 28)


def test_public_today_honours_configured_zone(monkeypatch):
    monkeypatch.setenv(PUBLIC_TIME_ZONE_ENV, "UTC")
    instant = datetime(2026, 7, 27, 20, 0, tzinfo=timezone.utc)

    assert public_time_zone_name() == "UTC"
    assert public_today(instant) == date(2026, 7, 27)


def test_invalid_public_zone_falls_back_to_almaty(monkeypatch):
    monkeypatch.setenv(PUBLIC_TIME_ZONE_ENV, "Invalid/Zone")
    instant = datetime(2026, 7, 27, 20, 0, tzinfo=timezone.utc)

    assert public_time_zone_name() == "Asia/Almaty"
    assert public_today(instant) == date(2026, 7, 28)
