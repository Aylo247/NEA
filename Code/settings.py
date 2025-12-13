from datetime import time, timedelta, date
import json
from PyQt5.QtGui import QColor

"""
This module defines the Settings and ThemeManager classes for managing application settings
and visual themes in a scheduling application.
"""

class Settings:
    #initializes default settings
    def __init__(self):
        self.theme = "light"
        self.start_time = time(7, 0)
        self.end_time = time(22, 0)
        self.notification_frequency = timedelta(minutes=30)
        self.meal_windows = {"Breakfast": (time(7,0), time(9,0)),
                             "Lunch": (time(12,0), time(14,0)),
                             "Dinner": (time(18,0), time(20,0))}
        self.break_durations = {"short": timedelta(minutes=10),
                                "long": timedelta(minutes=30)}
        self.history_duration = timedelta(days=7)
        self.holiday_ranges = []  # list of tuples (start_date, end_date)

    #converts the settings to and from a dictionary for easy JSON serialization by the PersistenceManager class
    def to_dict(self):
        settings_dict = {
            "theme": self.theme,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "notification_frequency": self.notification_frequency.total_seconds(),
            "meal_windows": {
                meal: (start.isoformat(), end.isoformat())
                for meal, (start, end) in self.meal_windows.items()
            },
            "break_durations": {
                name: duration.total_seconds() // 60  # in minutes
                for name, duration in self.break_durations.items()
            },
            "history_duration": self.history_duration.total_seconds() // 86400,  # in days
            "holiday_ranges": [
                (start.isoformat(), end.isoformat())
                for start, end in self.holiday_ranges
            ]
        }
        return settings_dict
    
    def from_dict(self, data):
        self.theme = data.get("theme", self.theme)
        self.start_time = time.fromisoformat(data.get("start_time", self.start_time.isoformat()))
        self.end_time = time.fromisoformat(data.get("end_time", self.end_time.isoformat()))
        self.notification_frequency = timedelta(seconds=data.get("notification_frequency", self.notification_frequency.total_seconds()))
        
        meal_windows_data = data.get("meal_windows", {})
        self.meal_windows = {
            meal: (time.fromisoformat(start), time.fromisoformat(end))
            for meal, (start, end) in meal_windows_data.items()
        }
        
        break_durations_data = data.get("break_durations", {})
        self.break_durations = {
            name: timedelta(minutes=duration)
            for name, duration in break_durations_data.items()
        }

        self.history_duration = timedelta(days=data.get("history_duration", self.history_duration.total_seconds() // 86400))
        holiday_ranges_data = data.get("holiday_ranges", [])
        self.holiday_ranges = [
            (date.fromisoformat(start), date.fromisoformat(end))
            for start, end in holiday_ranges_data
        ]

    #updates settings and saves them using the PersistenceManager
    def update(self, PersistenceManager, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        PersistenceManager.save_settings(self)

    #manages holiday ranges
    def add_holiday(self, start_date, end_date):
        self.holiday_ranges.append((start_date, end_date))

    def clean_past_holidays(self):
        today = date.today()
        self.holiday_ranges = [
            (start, end) for start, end in self.holiday_ranges
            if end >= today
        ]

class ThemeManager:
    """
    Manages application-wide visual themes.
    Loads static theme definitions from a JSON file
    and provides access to the active theme based on user settings.
    """

    def __init__(self, themes_file="themes.json"):
        self.themes_file = themes_file
        self.themes = self._load_themes()

    def _load_themes(self):
        try:
            with open(self.themes_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def get_theme(self, theme_name):
        """
        Returns a theme dictionary given a theme name from Settings.
        Falls back safely if the theme does not exist.
        """
        if not theme_name:
            return {}

        return self.themes.get(theme_name.lower(), {})

    def get_colour(self, theme_name, key, fallback="#000000"):
        """
        Convenience method to fetch a QColor directly.
        Prevents crashes if keys are missing.
        """
        theme = self.get_theme(theme_name)
        return QColor(theme.get(key, fallback))

