from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QScrollArea, QMainWindow, QLabel,
    QGroupBox, QFormLayout, QComboBox, QTimeEdit, QDateEdit, QPushButton,
    QMessageBox, QDialog, QCalendarWidget, QListWidget, QHBoxLayout
)
from PyQt5.QtGui import QPainter, QColor, QFont
from PyQt5.QtCore import Qt, QTime, QDate
from settings import ThemeManager
import sys
from datetime import timedelta




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

        self.theme_manager = ThemeManager()
        self.hour_line_colour = self.theme_manager.get_colour(self.theme_manager.theme, "hour_line")
        self.faint_line_colour = self.theme_manager.get_colour(self.theme_manager.theme, "faint_line")


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
    def __init__(self, settings, persistence_manager, theme_manager):
        super().__init__()

        self.settings = settings
        self.persistence = persistence_manager
        self.theme_manager = theme_manager

        # =======================
        # MAIN LAYOUT
        # =======================
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # =======================
        # GENERAL SETTINGS
        # =======================
        self.general_group = QGroupBox("general settings")
        self.general_form = QFormLayout()
        self.general_group.setLayout(self.general_form)
        self.main_layout.addWidget(self.general_group)

        # Theme combo box
        self.theme_box = QComboBox()
        self.theme_box.addItems(["light", "dark"])
        self.theme_box.setCurrentText(self.settings.theme)
        self.theme_box.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.theme_box.setMinimumWidth(100)
        self.theme_box.setStyleSheet(f"""
                        QComboBox {{
                            background-color: {self.theme_manager.get_colour(self.settings.theme, "groupbox_bg")};
                            color: {self.theme_manager.get_colour(self.settings.theme, "label_color")};
                            padding: 2px 4px;
                        }}
                        QComboBox QAbstractItemView {{
                            background-color: {self.theme_manager.get_colour(self.settings.theme, "groupbox_bg")};
                            color: {self.theme_manager.get_colour(self.settings.theme, "label_color")};
                            selection-background-color: {self.theme_manager.get_colour(self.settings.theme, "button_bg")   };
                        }}
                    """)
        self.general_form.addRow("theme", self.theme_box)

        # Weekday times
        self.start_time_edit = QTimeEdit(QTime(self.settings.start_time.hour, self.settings.start_time.minute))
        self.end_time_edit = QTimeEdit(QTime(self.settings.end_time.hour, self.settings.end_time.minute))
        self.general_form.addRow("weekday start time", self.start_time_edit)
        self.general_form.addRow("weekday end time", self.end_time_edit)

        # Weekend times
        self.weekend_start_edit = QTimeEdit(QTime(self.settings.start_time.hour, self.settings.start_time.minute))
        self.weekend_end_edit = QTimeEdit(QTime(self.settings.end_time.hour, self.settings.end_time.minute))
        self.general_form.addRow("weekend start time", self.weekend_start_edit)
        self.general_form.addRow("weekend end time", self.weekend_end_edit)

        # =======================
        # MEAL TIMES
        # =======================
        self.meal_group = QGroupBox("meal times")
        self.meal_form = QFormLayout()
        self.meal_group.setLayout(self.meal_form)
        self.main_layout.addWidget(self.meal_group)

        self.meal_edits = {}
        for meal, (start, end) in self.settings.meal_windows.items():
            start_edit = QTimeEdit(QTime(start.hour, start.minute))
            end_edit = QTimeEdit(QTime(end.hour, end.minute))
            self.meal_form.addRow(f"{meal} start".lower(), start_edit)
            self.meal_form.addRow(f"{meal} end".lower(), end_edit)
            self.meal_edits[meal] = (start_edit, end_edit)

        # =======================
        # HOLIDAYS
        # =======================
        self.holiday_group = QGroupBox("Holidays (max 3)")
        self.holiday_layout = QVBoxLayout()
        self.holiday_group.setLayout(self.holiday_layout)
        self.main_layout.addWidget(self.holiday_group)

        self.holiday_list_widget = QListWidget()
        self.holiday_list_widget.itemDoubleClicked.connect(self.edit_holiday)
        self.holiday_layout.addWidget(self.holiday_list_widget)
        self.refresh_holiday_list()

        btn_layout = QHBoxLayout()
        self.add_holiday_btn = QPushButton("Add holiday")
        self.remove_holiday_btn = QPushButton("Remove selected")
        self.add_holiday_btn.clicked.connect(self.add_holiday)
        self.remove_holiday_btn.clicked.connect(self.remove_selected_holiday)
        btn_layout.addWidget(self.add_holiday_btn)
        btn_layout.addWidget(self.remove_holiday_btn)
        self.holiday_layout.addLayout(btn_layout)

        # =======================
        # SAVE BUTTON
        # =======================
        self.save_btn = QPushButton("save settings")
        self.save_btn.clicked.connect(self.save_settings)
        self.main_layout.addWidget(self.save_btn)

        # =======================
        # HEADER FONT
        # =======================
        self.header_font = QFont()
        self.header_font.setPointSize(16)
        for group in [self.general_group, self.meal_group, self.holiday_group]:
            group.setFont(self.header_font)

        # =======================
        # SNAPSHOT
        # =======================
        self.original_state = self._snapshot()

        # =======================
        # CONNECT THEME CHANGE
        # =======================
        self.theme_box.currentTextChanged.connect(self.apply_theme)

        # Apply theme initially
        self.apply_theme()

    # =======================
    # STATE SNAPSHOT
    # =======================
    def _snapshot(self):
        meal_snapshot = {meal: (start.time().toPyTime(), end.time().toPyTime()) 
                         for meal, (start, end) in self.meal_edits.items()}
        holidays_snapshot = list(self.settings.holiday_ranges)
        return {
            "theme": self.theme_box.currentText(),
            "start_time": self.start_time_edit.time().toPyTime(),
            "end_time": self.end_time_edit.time().toPyTime(),
            "weekend_start": self.weekend_start_edit.time().toPyTime(),
            "weekend_end": self.weekend_end_edit.time().toPyTime(),
            "meal_windows": meal_snapshot,
            "holidays": holidays_snapshot
        }

    # =======================
    # SAVE LOGIC
    # =======================
    def save_settings(self):
        current_state = self._snapshot()

        # No changes → do nothing
        if current_state == self.original_state:
            return

        # Confirmation popup
        msg = QMessageBox(self)
        msg.setWindowTitle("confirm changes")
        msg.setText("you have unsaved changes. do you want to save them?")
        msg.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
        msg.setDefaultButton(QMessageBox.Save)
        response = msg.exec_()

        if response == QMessageBox.Save:
            self.apply_settings()
            self.original_state = self._snapshot()

    def apply_settings(self):
        self.settings.theme = self.theme_box.currentText()
        self.settings.start_time = self.start_time_edit.time().toPyTime()
        self.settings.end_time = self.end_time_edit.time().toPyTime()
        self.settings.weekend_start = self.weekend_start_edit.time().toPyTime()
        self.settings.weekend_end = self.weekend_end_edit.time().toPyTime()
        # Meal windows
        for meal, (start_edit, end_edit) in self.meal_edits.items():
            self.settings.meal_windows[meal] = (start_edit.time().toPyTime(), end_edit.time().toPyTime())
        self.persistence.save_settings(self.settings)

    # =======================
    # HOLIDAYS
    # =======================
    def add_holiday(self):
        if len(self.settings.holiday_ranges) >= 3:
            QMessageBox.warning(self, "max holidays", "you can only have up to 3 holidays.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("add holiday")
        layout = QVBoxLayout(dialog)

        calendar_start = QCalendarWidget()
        calendar_end = QCalendarWidget()
        layout.addWidget(QLabel("start date"))
        layout.addWidget(calendar_start)
        layout.addWidget(QLabel("end date"))
        layout.addWidget(calendar_end)

        save_btn = QPushButton("add")
        save_btn.clicked.connect(lambda: self.save_holiday(dialog, calendar_start, calendar_end))
        layout.addWidget(save_btn)

        dialog.setLayout(layout)
        dialog.exec_()

    def save_holiday(self, dialog, start_cal, end_cal):
        start_date = start_cal.selectedDate().toPyDate()
        end_date = end_cal.selectedDate().toPyDate()

        if start_date > end_date:
            QMessageBox.warning(self, "invalid range", "start date cannot be after end date.")
            return

        if len(self.settings.holiday_ranges) >= 3:
            QMessageBox.warning(self, "max holidays", "you can only have up to 3 holidays.")
            return

        self.settings.add_holiday(start_date, end_date)
        self.refresh_holiday_list()  # update display
        dialog.accept()

    def edit_holiday(self, item):
        index = self.holiday_list_widget.row(item)
        start, end = self.settings.holiday_ranges[index]

        dialog = QDialog(self)
        dialog.setWindowTitle("edit Holiday")
        layout = QVBoxLayout(dialog)

        calendar_start = QCalendarWidget()
        calendar_end = QCalendarWidget()
        calendar_start.setSelectedDate(QDate(start.year, start.month, start.day))
        calendar_end.setSelectedDate(QDate(end.year, end.month, end.day))
        
        layout.addWidget(QLabel("start date"))
        layout.addWidget(calendar_start)
        layout.addWidget(QLabel("end date"))
        layout.addWidget(calendar_end)

        save_btn = QPushButton("save")
        save_btn.clicked.connect(lambda: self.save_edited_holiday(dialog, index, calendar_start, calendar_end))
        layout.addWidget(save_btn)

        dialog.setLayout(layout)
        dialog.exec_()

    def save_edited_holiday(self, dialog, index, start_cal, end_cal):
        start_date = start_cal.selectedDate().toPyDate()
        end_date = end_cal.selectedDate().toPyDate()

        if start_date > end_date:
            QMessageBox.warning(self, "invalid range", "start date cannot be after end date.")
            return

        # Update the holiday in settings
        self.settings.holiday_ranges[index] = (start_date, end_date)
        self.refresh_holiday_list()
        dialog.accept()

    def remove_selected_holiday(self):
        selected_items = self.holiday_list_widget.selectedItems()
        if not selected_items:
            return
        for item in selected_items:
            index = self.holiday_list_widget.row(item)
            del self.settings.holiday_ranges[index]
        self.refresh_holiday_list()

    def refresh_holiday_list(self):
        self.holiday_list_widget.clear()
        for start, end in self.settings.holiday_ranges:
            self.holiday_list_widget.addItem(f"{start} → {end}")

    # =======================
    # THEME HANDLING
    # =======================
    def apply_theme(self):
        theme_name = self.theme_box.currentText().lower()
        t = self.theme_manager.get_theme(theme_name)

        if not t:  # fallback if theme not found
            print(f"Theme '{theme_name}' not found. Using light theme as default.")
            t = self.theme_manager.get_theme("light")

        # Set main window background & default text color
        self.setStyleSheet(f"background-color: {t['background']}; color: {t['label_color']};")

        # Group boxes
        for groupbox in [self.general_group, self.meal_group, self.holiday_group]:
            groupbox.setStyleSheet(f"""
                QGroupBox {{
                    background-color: {t['groupbox_bg']};
                    border: 1px solid {t['border_color']};
                    border-radius: 8px;
                    margin-top: 10px;
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 5px;
                    color: {t['label_color']};
                }}
            """)

        # Buttons
        for btn in [self.add_holiday_btn, self.remove_holiday_btn, self.save_btn]:
            btn.setStyleSheet(f"""
                QPushButton {{
                    border-radius: 8px;
                    padding: 6px 12px;
                    background-color: {t['button_bg']};
                    color: {t['button_fg']};
                    border: 1px solid {t['border_color']};
                }}
                QPushButton:hover {{
                    background-color: {t['button_hover']};
                }}
            """)

        # Labels
        for label in self.findChildren(QLabel):
            label.setStyleSheet(f"color: {t['label_color']}")

        # QTimeEdit and QDateEdit arrows and text
        for time_edit in self.findChildren(QTimeEdit) + self.findChildren(QDateEdit):
            time_edit.setStyleSheet(f"""
                QTimeEdit, QDateEdit {{
                    background-color: {t['groupbox_bg']};
                    color: {t['label_color']};
                    border: 1px solid {t['border_color']};
                    border-radius: 4px;
                    padding: 2px;
                }}
                QTimeEdit::up-button, QTimeEdit::down-button,
                QDateEdit::up-button, QDateEdit::down-button {{
                    subcontrol-origin: border;
                    subcontrol-position: right;
                    width: 16px;
                    background-color: {t['button_bg']};
                }}
                QTimeEdit::up-button:hover, QTimeEdit::down-button:hover,
                QDateEdit::up-button:hover, QDateEdit::down-button:hover {{
                    background-color: {t['button_hover']};
                }}
            """)




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

