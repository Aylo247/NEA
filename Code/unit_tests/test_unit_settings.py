from datetime import time, timedelta, date, datetime
from settings import Settings


def test_settings_defaults():
    s = Settings()

    assert s.theme == "light"
    assert s.start_time == time(7, 0)
    assert s.end_time == time(22, 0)
    assert s.weekend_start == time(9, 0)
    assert s.weekend_end == time(23, 0)
    assert s.notification_frequency == timedelta(minutes=30)
    assert s.break_duration == timedelta(minutes=30)
    assert s.break_interval == timedelta(minutes=90)
    assert s.meal_duration == timedelta(minutes=30)
    assert s.holiday_ranges == []


def test_settings_to_dict():
    s = Settings()
    data = s.to_dict()

    assert data["theme"] == "light"
    assert data["start_time"] == "07:00:00"
    assert data["end_time"] == "22:00:00"
    assert data["notification_frequency"] == 30
    assert "meal_windows" in data
    assert "breakfast" in data["meal_windows"]


def test_settings_from_dict():
    s = Settings()
    data = {
        "theme": "dark",
        "start_time": "08:00:00",
        "end_time": "20:00:00",
        "notification_frequency": 15,
        "break_duration": 20
    }

    s.from_dict(data)

    assert s.theme == "dark"
    assert s.start_time == time(8, 0)
    assert s.end_time == time(20, 0)
    assert s.notification_frequency == timedelta(minutes=15)
    assert s.break_duration == timedelta(minutes=20)


def test_settings_from_partial_dict_uses_defaults():
    s = Settings()
    s.from_dict({"theme": "dark"})

    assert s.theme == "dark"
    assert s.start_time == time(7, 0)
    assert s.end_time == time(22, 0)


def test_add_and_detect_holiday():
    s = Settings()
    today = date.today()
    tomorrow = today + timedelta(days=1)

    s.add_holiday(today, tomorrow)

    assert s.is_holiday(today) is True
    assert s.is_holiday(tomorrow) is True


def test_clean_past_holidays():
    s = Settings()
    past_start = date.today() - timedelta(days=10)
    past_end = date.today() - timedelta(days=5)
    future_start = date.today()
    future_end = date.today() + timedelta(days=5)

    s.holiday_ranges = [
        (past_start, past_end),
        (future_start, future_end)
    ]

    s.clean_past_holidays()

    assert len(s.holiday_ranges) == 1
    assert s.holiday_ranges[0] == (future_start, future_end)


def test_get_day_bounds_weekday():
    s = Settings()
    dt = datetime(2026, 1, 6)  # Tuesday

    start, end = s.get_day_bounds(dt)

    assert start.time() == s.start_time
    assert end.time() == s.end_time


def test_get_day_bounds_weekend():
    s = Settings()
    dt = datetime(2026, 1, 4)  # Sunday

    start, end = s.get_day_bounds(dt)

    assert start.time() == s.weekend_start
    assert end.time() == s.weekend_end
