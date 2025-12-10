from PyQt5.QtWidgets import QMainWindow, QWidget, QStackedWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt


class ScheduleView(QWidget):
    def __init__(self, schedule):
        super().__init__()
        self.schedule = schedule

        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel("Schedule View (placeholder)"))
        self.setLayout(self.layout)

class ScheduleViewDay(ScheduleView):
    def __init__(self, schedule, date):
        super().__init__(schedule)
        self.day = self.schedule.day(date)

        self.layout.addWidget(QLabel(f"Schedule View for {date} (placeholder)"))

class ScheduleViewWeek(ScheduleView):
    def __init__(self, schedule, week_start_date):
        super().__init__(schedule)
        self.day = self.schedule.week(week_start_date)

        self.layout.addWidget(QLabel(f"Schedule View for week commencing {week_start_date} (placeholder)"))

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


    def setup_connections(self):
        pass

    def switch_to_scheduleDay(self):
        pass

    def switch_to_scheduleWeek(self):
        pass

    def switch_to_todo(self):
        pass

    def switch_to_settings(self):
        pass

    def pop_up_confirm(self):
        pass
