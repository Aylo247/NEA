from datetime import time, timedelta, date, datetime
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
        self.weekend_start = time(9, 0)
        self.weekend_end = time(23, 0)
        self.notification_frequency = timedelta(minutes=30)
        self.meal_windows = {"breakfast": (time(7,0), time(9,0)),
                             "lunch": (time(12,0), time(14,0)),
                             "dinner": (time(18,0), time(20,0))}
        self.break_duration = timedelta(minutes=30)
        self.break_interval = timedelta(minutes=90)
        self.meal_duration = timedelta(minutes=30)
        self.history_duration = timedelta(days=7)
        self.holiday_ranges = []  # list of tuples (start_date, end_date)

    #converts the settings to and from a dictionary for easy JSON serialization by the PersistenceManager class
    def to_dict(self):
        settings_dict = {
            "theme": self.theme,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "weekend_start": self.weekend_start.isoformat(),
            "weekend_end": self.weekend_end.isoformat(),
            "notification_frequency": self.notification_frequency.total_seconds() // 60, #in minutes
            "meal_windows": {
                meal: (start.isoformat(), end.isoformat())
                for meal, (start, end) in self.meal_windows.items()
            },
            "break_duration": self.break_duration.total_seconds() // 60,  # in minutes,
            "history_duration": self.history_duration.total_seconds() // 86400,  # in days
            "break_interval": self.break_interval.total_seconds() // 60, # in minutes,
            "meal_duration": self.meal_duration.total_seconds() // 60, # in minutes,
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
        self.weekend_start = time.fromisoformat(data.get("weekend_start", self.weekend_start.isoformat()))
        self.weekend_end = time.fromisoformat(data.get("weekend_end", self.weekend_end.isoformat()))
        nf = data.get("notification_frequency")
        self.notification_frequency = timedelta(minutes=nf)
        
        meal_windows_data = data.get("meal_windows", {})
        self.meal_windows = {
            meal: (time.fromisoformat(start), time.fromisoformat(end))
            for meal, (start, end) in meal_windows_data.items()
        }
        
        break_duration_data = data.get("break_duration")
        self.break_duration = timedelta(minutes=break_duration_data)
        break_interval_data = data.get("break_interval")
        self.break_interval = timedelta(minutes=break_interval_data)

        meal_duration_data = data.get("meal_duration")
        self.meal_duration = timedelta(minutes=meal_duration_data)

        self.history_duration = timedelta(days=data.get("history_duration", self.history_duration.total_seconds() // 86400))
        holiday_ranges_data = data.get("holiday_ranges", [])
        self.holiday_ranges = [
            (date.fromisoformat(start), date.fromisoformat(end))
            for start, end in holiday_ranges_data
        ]

    #updates settings and saves them using the PersistenceManager
    def update(self, persistenceManager, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        persistenceManager.save_settings(self)

    #manages holiday ranges
    def add_holiday(self, start_date, end_date):
        self.holiday_ranges.append((start_date, end_date))

    def clean_past_holidays(self):
        today = date.today()
        self.holiday_ranges = [
            (start, end) for start, end in self.holiday_ranges
            if end >= today
        ]
    
    def is_holiday(self, check_date):
        for start, end in self.holiday_ranges:
            if start <= check_date.date() <= end:
                return True
        return False

    def get_day_bounds(self, dt):
        # weekday: 0=Mon, 6=Sun
        weekday = dt.weekday()
        if self.is_holiday(dt) or weekday >= 5:
            start = datetime.combine(dt.date(), self.weekend_start)
            end = datetime.combine(dt.date(), self.weekend_end)
        else:
            start = datetime.combine(dt.date(), self.start_time)
            end = datetime.combine(dt.date(), self.end_time)
        return start, end

class ThemeManager:
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
        if not theme_name:
            return {}
        t = self.themes.get(theme_name.lower(), {})
        return self.theme_to_qss(t)
    
    def get_theme_dict(self, theme_name):
        if not theme_name:
            return {}
        return self.themes.get(theme_name.lower(), {})
    
    def theme_to_qss(self, theme):
        return f""" {{
            font-family: "{theme['font']}";
        }}

        QMainWindow {{
            background-color: {theme['window_bg']};
        }}

        QWidget {{
            background-color: {theme['background']};
        }}

        QGroupBox {{
            background-color: {theme['groupbox_bg']};
            border: 1px solid {theme['border_color']};
            border-radius: 6px;
            margin-top: 6px;
        }}

        QLabel {{
            color: {theme.get('label_color', '#000000')};
        }}

        QPushButton {{
            background-color: {theme['button_bg']};
            color: {theme['button_fg']};
            border: 1px solid {theme['border_color']};
            border-radius: 6px;
            padding: 6px 10px;
        }}

        QPushButton:hover {{
            background-color: {theme['button_hover']};
        }}

        QLineEdit, QTextEdit, QComboBox {{
            color: {theme.get('label_color', '#000000')};
            background-color: {theme['window_bg']};
        }}
        """


    def get_colour(self, theme_name, key, fallback="#000000"):
        theme = self.get_theme_dict(theme_name)
        return QColor(theme.get(key, fallback))

    def get_font(self, theme_name, fallback="Arial"):
        theme = self.get_theme_dict(theme_name)
        return theme.get("font", fallback)
