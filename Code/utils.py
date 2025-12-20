from PyQt5.QtWidgets import QMessageBox, QLabel, QGroupBox, QPushButton, QTimeEdit, QDateEdit, QComboBox, QApplication
from PyQt5.QtCore import QTime
from datetime import datetime, timedelta, time


class IndexStack():
    def __init__(self):
        self.stack = []

    @property
    def length(self):
        return len(self.stack)

    def add_item(self, item):
        if self.length >= 5:
            self.stack.pop(0)
        self.stack.append(item)

    def pop_item(self):
        try:
            return self.stack.pop()
        except IndexError:
            return None
        
    def peek_top(self):
        return self.stack[self.length-1]

class GUIUtils():
    def __init__(self, theme_manager, settings):
        self.tm = theme_manager
        self.settings = settings

    @staticmethod
    def round_to_5(qtime):
        # Convert QTime → datetime.time
        dt = datetime.combine(datetime.today(), time(qtime.hour(), qtime.minute(), qtime.second()))
        discard = timedelta(minutes=dt.minute % 5, seconds=dt.second, microseconds=dt.microsecond)
        dt -= discard
        if discard >= timedelta(minutes=2.5):
            dt += timedelta(minutes=5)
        # Convert back to QTime
        return QTime(dt.hour, dt.minute)

    @staticmethod
    def pop_up_confirm(parent, message: str) -> bool:
        reply = QMessageBox.question(
            parent,
            "Confirm",
            message,
            QMessageBox.Yes | QMessageBox.No
        )
        return reply == QMessageBox.Yes

    def apply_theme(self, theme = None):
        if theme is None:
            theme_name = getattr(self.settings, "theme", None) or self.settings.get("theme", "light")
        else:
            theme_name = theme
        t = self.tm.get_theme(theme_name)
        if not t:
            t = self.tm.get_theme("light")
        app = QApplication.instance()
        app.setStyleSheet(t)
