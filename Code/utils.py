from PyQt5.QtWidgets import (
    QMessageBox, QPushButton, QHBoxLayout, QWidget,
    QApplication)
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
        
    @staticmethod
    def create_top_bar(*,
                       show_back=False,
                       show_settings=False,
                       show_todo=False):
        bar = QWidget()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 12, 12, 6)

        buttons = {}

        if show_back:
            buttons["back"] = QPushButton("← Back")
            layout.addWidget(buttons["back"])

        layout.addStretch()

        if show_todo:
            buttons["todo"] = QPushButton("To-Do")
            layout.addWidget(buttons["todo"])

        if show_settings:
            buttons["settings"] = QPushButton("⚙")
            layout.addWidget(buttons["settings"])

        return bar, buttons

