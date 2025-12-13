from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QScrollArea, QMainWindow, QLabel
from PyQt5.QtGui import QPainter, QColor, QFont
from PyQt5.QtCore import Qt
from settings import ThemeManager
import sys




class ScheduleView(QWidget):
    def __init__(self, schedule):
        super().__init__()
        self.schedule = schedule

        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel("Schedule View (placeholder)"))
        self.setLayout(self.layout)

    
class DayContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # constants
        self.hour_height = 120
        self.main_line_height = 2
        self.faint_line_height = 1
        self.num_faint_lines = 3
        self.segment_spacing = (self.hour_height - self.main_line_height - (self.faint_line_height * self.num_faint_lines)) / (self.num_faint_lines + 1)

        self.setMinimumHeight(24 * self.hour_height)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setFont(QFont("Arial", 12))


        for hour in range(24):
            y_start = int(hour * self.hour_height)

            # MAIN hour line (dark gray)
            painter.fillRect(50, y_start, self.width()-50, self.main_line_height, QColor(128,128,128))

            # Faint lines (light gray)
            current_y = y_start + self.main_line_height
            for _ in range(self.num_faint_lines):
                current_y += self.segment_spacing
                painter.fillRect(50, int(current_y), self.width()-50, self.faint_line_height,  QColor(100,100,100))
                current_y += self.faint_line_height

            # HOUR NUMBER (aligned next to main line)
            text_y = int(y_start + self.main_line_height/2 + 4)  # vertically centered with main line
            painter.setPen(QColor(128,128,128))
            painter.drawText(5, text_y, f"{hour:02d}:00")

class DayView(QWidget):
    def __init__(self):
        super().__init__()
        self.setGeometry(300, 100, 350, 900)
        self.setWindowTitle("Day View Left Side")

        from theme_manager import ThemeManager

# somewhere in DayContainer or DayView setup
        self.theme_manager = ThemeManager()
        self.hour_line_colour = self.theme_manager.get_colour(self.settings.theme, "hour_line")
        self.faint_line_colour = self.theme_manager.get_colour(self.settings.theme, "faint_line")


        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        container = DayContainer()
        scroll.setWidget(container)
        self.show()

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
    def __init__(self, schedule, settings, persistence_manager):
        super().__init__()

        self.schedule = schedule
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
