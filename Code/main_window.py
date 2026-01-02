from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QMainWindow, QMessageBox, QStackedWidget
)
from utils import IndexStack
from other_views import ToDoListView, MonthView
from day_view_container import DayViewContainer
from settings_view import SettingsView
from week_view import WeekViewContainer

class MainWindow(QMainWindow):
    """main application window containing all views and navigation logic"""
    
    def __init__(self, schedule, settings, persistence_manager, util, customs) -> None:
        """initialize main window, set up views, and configure navigation"""
        super().__init__()
        self.util = util
        self.schedule = schedule
        self.settings = settings
        self.persistence = persistence_manager
        self.customs = customs

        self.index_stack = IndexStack()
        self.current_index = 0

        # minimum size
        self.setMinimumSize(1200, 700)  

        # central widget
        self.central = QWidget()
        self.central.setObjectName("central")
        self.setCentralWidget(self.central)

        self.main_layout = QVBoxLayout(self.central)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(12)

        # stack for screens
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)

        # screens
        self.todo_view = ToDoListView(self.schedule, self.util)
        self.settings_view = SettingsView(self.settings, self.persistence, self.util)
        self.month_view = MonthView(self.schedule, self.util)
        self.day_view_container = DayViewContainer(self.schedule, self.util, self.customs)
        self.week_view_container = WeekViewContainer(self.schedule, self.util)

        self.stack.addWidget(self.month_view)
        self.stack.addWidget(self.settings_view)
        self.stack.addWidget(self.todo_view)
        self.stack.addWidget(self.day_view_container)
        self.stack.addWidget(self.week_view_container)

        # navigation
        self.todo_view.open_settings.connect(lambda: self.switch_to(1))
        self.todo_view.back.connect(lambda: self.switch_back())
        self.settings_view.back.connect(lambda: self.switch_back())
        self.month_view.open_settings.connect(lambda: self.switch_to(1))
        self.month_view.open_todo.connect(lambda: self.switch_to(2))
        self.month_view.open_day.connect(self.day_view_container.set_current_day)
        self.month_view.open_day.connect(lambda _: self.switch_to(3))
        self.month_view.open_week.connect(self.week_view_container.set_current_week)
        self.month_view.open_week.connect(lambda _: self.switch_to(4))
        self.month_view.back.connect(lambda: self.switch_back())
        self.day_view_container.back.connect(lambda: self.switch_back())
        self.day_view_container.open_settings.connect(lambda: self.switch_to(1))
        self.day_view_container.open_todo.connect(lambda: self.switch_to(2))
        self.day_view_container.open_month.connect(self.month_view.change_to_month)
        self.day_view_container.open_month.connect(lambda: self.switch_to(0))
        self.day_view_container.open_week.connect(self.week_view_container.set_current_week)
        self.day_view_container.open_week.connect(lambda _: self.switch_to(4))
        self.week_view_container.open_settings.connect(lambda: self.switch_to(1))
        self.week_view_container.open_todo.connect(lambda: self.switch_to(2))
        self.week_view_container.open_day.connect(self.day_view_container.set_current_day)
        self.week_view_container.open_day.connect(lambda _: self.switch_to(3))
        self.week_view_container.open_month.connect(self.month_view.change_to_month)
        self.week_view_container.open_month.connect(lambda _: self.switch_to(0))
        self.week_view_container.back.connect(lambda: self.switch_back())
        self.setObjectName("MainWindow")

        # apply themes
        self.util.apply_theme()

    def switch_to(self, index: int) -> None:
        """switch to a given screen index and refresh the widget if possible"""
        self.schedule.clear_history()
        if index != self.current_index:
            self.index_stack.add_item(self.current_index)

        self.stack.setCurrentIndex(index)
        self.current_index = index

        widget = self.stack.currentWidget()
        if hasattr(widget, "refresh"):
            widget.refresh()

    def switch_back(self) -> None:
        """switch back to the previous screen, showing a warning if impossible"""
        self.schedule.clear_history()
        popped = self.index_stack.pop_item()
        if popped is None:
            QMessageBox.warning(self, "oopsie woopsie!", "cannot go back anymore")
        else:
            self.stack.setCurrentIndex(popped)
            self.current_index = popped

            widget = self.stack.currentWidget()
            if hasattr(widget, "refresh"):
                widget.refresh()

    def closeEvent(self, event):
        # if currently in settings view, commit settings first
        if self.current_index == 1 and hasattr(self, "settings_view"):
            self.settings_view.save_settings()

        # then save everything
        try:
            self.persistence.save_all(self.schedule, self.settings, self.customs)
        except Exception as e:
            # optional: show an error dialog if saving fails
            QMessageBox.warning(self, "Save Error", f"Failed to save data: {e}")
            event.ignore()
            return

        # only accept event if save succeeded
        event.accept()
