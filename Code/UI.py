from PyQt6.QtWidgets import QMainWindow, QWidget, QStackedWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

class ScheduleView(QWidget):
    def __init__(self, schedule):
        super().__init_()
        self.schedule = schedule

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Schedule View (placeholder)"))
        self.setLayout(layout)

class ScheduleViewDay(ScheduleView):
    def __init__(self, schedule, date):
        super().__init__(schedule)
        self.day = self.sechdule.day(date)

        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Schedule View for Today (placeholder)"))
        self.setLayout(layout)

class ToDoListView(QWidget):
    def __init__(self, todo_list):
        super().__init__()
        self.todo_list = todo_list

        layout = QVBoxLayout()
        layout.addWidget(QLabel("To-Do List View (placeholder)"))
        self.setLayout(layout)

class SettingsView(QWidget):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Settings View (placeholder)"))
        self.setLayout(layout)




class MainWindow(QMainWindow):
    def __init__(self, schedule, todo_list, settings, persistence_manager):
        super().__init__()

        self.schedule = schedule
        self.todo_list = todo_list
        self.settings = settings
        self.persistence = persistence_manager

        self.setWindowTitle("Smart Day Planner")
        self.setMinimumSize(900, 600)

        # Stack for switching views (Schedule / To-do / Settings)
        self.stack = QStackedWidget()

        self.schedule_view = ScheduleView(self.schedule)
        self.todo_list_view = ToDoListView(self.todo_list)
        self.settings_view = SettingsView(self.settings)

        self.stack.addWidget(self.schedule_view)
        self.stack.addWidget(self.todo_list_view)
        self.stack.addWidget(self.settings_view)

        self.setCentralWidget(self.stack)

        self.setup_connections()

    def setup_connections(self):
        pass

    def switch_to_schedule(self):
        self.stack.setCurrentWidget(self.schedule_view)

    def switch_to_todo(self):
        self.stack.setCurrentWidget(self.todo_list_view)

    def switch_to_settings(self):
        self.stack.setCurrentWidget(self.settings_view)
