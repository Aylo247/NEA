from PyQt5.QtWidgets import (
    QMessageBox, QPushButton, QHBoxLayout, QWidget,
    QApplication, QTimeEdit
)
from PyQt5.QtCore import QDateTime
from datetime import timedelta, datetime
from typing import Any, Dict, Tuple, Optional


class IndexStack:
    """
    a fixed-length stack that stores up to 5 items
    older items are discarded when the stack exceeds its limit
    """
    def __init__(self) -> None:
        self.stack: list[Any] = []

    @property
    def length(self) -> int:
        """return the number of items in the stack"""
        return len(self.stack)

    def add_item(self, item: Any) -> None:
        """add a new item to the stack, removing the oldest if necessary"""
        if self.length >= 5:
            self.stack.pop(0)
        self.stack.append(item)

    def pop_item(self) -> Optional[Any]:
        """pop the most recent item from the stack, or return None if empty"""
        try:
            return self.stack.pop()
        except IndexError:
            return None

    def peek_top(self) -> Optional[Any]:
        """return the top item without removing it, or None if empty"""
        return self.stack[-1] if self.stack else None


class GUIUtils:
    """
    utility methods for GUI operations, including:
    - rounding QDateTime
    - pop-up confirmations
    - theme application
    - creating a top navigation bar
    """
    def __init__(self, theme_manager, settings) -> None:
        self.tm = theme_manager
        self.settings = settings

    @staticmethod
    def round_qdatetime_to_5(qdt: QDateTime) -> QDateTime:
        """
        round a QDateTime to the nearest 5-minute mark.
        if the remainder is >= 2.5 minutes, round up; otherwise round down
        """
        py = qdt.toPyDateTime()
        discard = timedelta(
            minutes=py.minute % 5,
            seconds=py.second,
            microseconds=py.microsecond
        )
        py -= discard
        if discard >= timedelta(minutes=2.5):
            py += timedelta(minutes=5)
        return QDateTime(py)

    @staticmethod
    def snap_to_5_minutes(value: int) -> int:
        """snap an integer minute value to the nearest lower multiple of 5"""
        return (value // 5) * 5

    @staticmethod
    def pop_up_confirm(parent: QWidget, message: str) -> bool:
        """show a confirmation dialog with Yes/No options"""
        reply = QMessageBox.question(
            parent,
            "confirm",
            message,
            QMessageBox.Yes | QMessageBox.No
        )
        return reply == QMessageBox.Yes

    def apply_theme(self, theme: Optional[str] = None) -> None:
        """apply a theme to the application"""
        if theme is None:
            theme_name = getattr(self.settings, "theme", "light")
        else:
            theme_name = theme

        t = self.tm.get_theme(theme_name) or self.tm.get_theme("light")
        app = QApplication.instance()
        if app:
            app.setStyleSheet(t)

    def get_day_bounds(self, date_obj: datetime) -> tuple:
        """get the start and end bounds of a day using settings """
        return self.settings.get_day_bounds(date_obj)

    @staticmethod
    def create_top_bar(*,
                       show_back: bool = False,
                       show_settings: bool = False,
                       show_todo: bool = False,
                       show_month: bool = False,
                       show_week: bool = False
                       ) -> tuple:
        """create a top navigation bar with optional buttons"""
        bar = QWidget()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 12, 12, 6)

        buttons: Dict[str, QPushButton] = {}

        if show_back:
            buttons["back"] = QPushButton("← back")
            layout.addWidget(buttons["back"])

        layout.addStretch()

        if show_month:
            buttons["month"] = QPushButton("month view")
            layout.addWidget(buttons["month"])

        if show_week:
            buttons["week"] = QPushButton("week view")
            layout.addWidget(buttons["week"])

        if show_todo:
            buttons["todo"] = QPushButton("to-do")
            layout.addWidget(buttons["todo"])

        if show_settings:
            buttons["settings"] = QPushButton("⚙")
            layout.addWidget(buttons["settings"])

        return bar, buttons


class FiveMinuteTimeEdit(QTimeEdit):
    """
    QTimeEdit widget that increments/decrements by 5-minute steps
    """
    def stepBy(self, steps: int) -> None:
        """override stepBy to change time in 5-minute increments"""
        new_time = self.time().addSecs(steps * 5 * 60)
        self.setTime(new_time)
