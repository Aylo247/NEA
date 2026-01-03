from datetime import time, timedelta, date, datetime
from typing import List, Tuple, Dict, Optional

class Settings:
    """
    stores user-configurable settings for the scheduling application, including:
    - working hours for weekdays and weekends
    - notification frequency
    - meal windows and break durations
    - holiday ranges
    provides methods to serialize/deserialize settings for JSON storage
    """
    
    def __init__(self) -> None:
        """initializes default settings values."""
        self.theme = "light"
        self.start_time = time(7, 0)
        self.end_time = time(22, 0)
        self.weekend_start = time(9, 0)
        self.weekend_end = time(23, 0)
        self.notification_frequency = timedelta(minutes=30)
        self.meal_windows = {
            "breakfast": (time(7, 0), time(9, 0)),
            "lunch": (time(12, 0), time(14, 0)),
            "dinner": (time(18, 0), time(20, 0))
        }
        self.break_duration = timedelta(minutes=30)
        self.break_interval = timedelta(minutes=90)
        self.meal_duration = timedelta(minutes=30)
        self.history_duration = timedelta(days=7)
        self.holiday_ranges: List[Tuple[date, date]] = []  # list of tuples (start_date, end_date)

    def to_dict(self) -> dict:
        """convert the settings into a dictionary suitable for JSON serialization"""
        return {
            "theme": self.theme,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "weekend_start": self.weekend_start.isoformat(),
            "weekend_end": self.weekend_end.isoformat(),
            "notification_frequency": self.notification_frequency.total_seconds() // 60,
            "meal_windows": {
                meal: (start.isoformat(), end.isoformat())
                for meal, (start, end) in self.meal_windows.items()
            },
            "break_duration": self.break_duration.total_seconds() // 60,
            "break_interval": self.break_interval.total_seconds() // 60,
            "meal_duration": self.meal_duration.total_seconds() // 60,
            "history_duration": self.history_duration.total_seconds() // 86400,
            "holiday_ranges": [
                (start.isoformat(), end.isoformat())
                for start, end in self.holiday_ranges
            ]
        }

    def from_dict(self, data: dict) -> None:
        """load settings from a dictionary (typically read from JSON)"""
        self.theme = data.get("theme", self.theme)
        self.start_time = time.fromisoformat(data.get("start_time", self.start_time.isoformat()))
        self.end_time = time.fromisoformat(data.get("end_time", self.end_time.isoformat()))
        self.weekend_start = time.fromisoformat(data.get("weekend_start", self.weekend_start.isoformat()))
        self.weekend_end = time.fromisoformat(data.get("weekend_end", self.weekend_end.isoformat()))
        
        nf = data.get("notification_frequency", self.notification_frequency.total_seconds() // 60)
        self.notification_frequency = timedelta(minutes=nf)

        meal_windows_data = data.get("meal_windows", {})
        self.meal_windows = {
            meal: (time.fromisoformat(start), time.fromisoformat(end))
            for meal, (start, end) in meal_windows_data.items()
        }

        self.break_duration = timedelta(minutes=data.get("break_duration", self.break_duration.total_seconds() // 60))
        self.break_interval = timedelta(minutes=data.get("break_interval", self.break_interval.total_seconds() // 60))
        self.meal_duration = timedelta(minutes=data.get("meal_duration", self.meal_duration.total_seconds() // 60))
        self.history_duration = timedelta(days=data.get("history_duration", self.history_duration.total_seconds() // 86400))
        
        holiday_ranges_data = data.get("holiday_ranges", [])
        self.holiday_ranges = [
            (date.fromisoformat(start), date.fromisoformat(end))
            for start, end in holiday_ranges_data
        ]

    def update(self, persistenceManager, **kwargs) -> None:
        """update multiple settings at once and persist changes"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        persistenceManager.save_settings(self)

    def add_holiday(self, start_date: date, end_date: date) -> None:
        """sdd a new holiday range"""
        self.holiday_ranges.append((start_date, end_date))

    def clean_past_holidays(self) -> None:
        """remove holidays that have already ended"""
        today = date.today()
        self.holiday_ranges = [(start, end) for start, end in self.holiday_ranges if end >= today]

    def is_holiday(self, check_date: date) -> bool:
        """check if a given date is a holiday """
        for start, end in self.holiday_ranges:
            if start <= check_date <= end:
                return True
        return False

    def get_day_bounds(self, dt: datetime | date) -> tuple:
        """get the start and end times for a given day"""
        if isinstance(dt, datetime):
            dt_date = dt.date()
        else:
            dt_date = dt

        weekday = dt_date.weekday()  # 0=monday, 6=sunday
        if self.is_holiday(dt_date) or weekday >= 5:
            start = datetime.combine(dt_date, self.weekend_start)
            end = datetime.combine(dt_date, self.weekend_end)
        else:
            start = datetime.combine(dt_date, self.start_time)
            end = datetime.combine(dt_date, self.end_time)
        return start, end
