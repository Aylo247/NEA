from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QMainWindow, QMessageBox, QStackedWidget
)
from utils import IndexStack
from other_veiws import ToDoListView, MonthView
from day_view_container import DayViewContainer
from settings_view import SettingsView

class MainWindow(QMainWindow):
    def __init__(self, schedule, settings, persistence_manager, util):
        super().__init__()
        self.util = util
        self.schedule = schedule
        self.settings = settings
        self.persistence = persistence_manager


        self.index_stack = IndexStack()
        self.current_index = 0

        # Central widget
        self.central = QWidget()
        self.setCentralWidget(self.central)

        self.main_layout = QVBoxLayout(self.central)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(12)

        # Stack for screens
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)

        # Screens
        self.todo_view = ToDoListView(self.schedule, self.util)
        self.settings_view = SettingsView(self.settings, self.persistence, self.util)
        self.month_view = MonthView(self.schedule, self.util)
        self.day_view_container = DayViewContainer(self.schedule, self.util)

        self.stack.addWidget(self.month_view)
        self.stack.addWidget(self.settings_view)
        self.stack.addWidget(self.todo_view)
        self.stack.addWidget(self.day_view_container)

        # Navigation
        self.todo_view.open_settings.connect(lambda: self.switch_to(1))
        self.todo_view.back.connect(lambda: self.switch_back())
        self.settings_view.back.connect(lambda: self.switch_back())
        self.month_view.open_settings.connect(lambda: self.switch_to(1))
        self.month_view.open_todo.connect(lambda: self.switch_to(2))
        self.month_view.open_day.connect(self.day_view_container.set_current_day)
        self.month_view.open_day.connect(lambda _: self.switch_to(3))
        self.month_view.back.connect(lambda: self.switch_back())
        self.day_view_container.back.connect(lambda: self.switch_back())
        self.day_view_container.open_settings.connect(lambda: self.switch_to(1))
        self.day_view_container.open_todo.connect(lambda: self.switch_to(2))
        self.day_view_container.open_month.connect(lambda: self.switch_to(0))


        # Apply themes
        self.util.apply_theme()

    def switch_to(self, index):
        if index != self.current_index:
            self.index_stack.add_item(self.current_index)

        self.stack.setCurrentIndex(index)
        self.current_index = index

        widget = self.stack.currentWidget()
        if hasattr(widget, "refresh"):
            widget.refresh()

    def switch_back(self):
        popped = self.index_stack.pop_item()
        if popped is None:
            QMessageBox.warning(self, "oopsie woopsie", "cannot go back anymore")
        else:
            self.stack.setCurrentIndex(popped)
            self.current_index = popped

            widget = self.stack.currentWidget()
            if hasattr(widget, "refresh"):
                widget.refresh()


