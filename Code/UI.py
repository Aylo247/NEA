from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QScrollArea, QMainWindow, QLabel,
    QGroupBox, QFormLayout, QComboBox, QTimeEdit, QDateEdit, QPushButton,
    QMessageBox, QDialog, QCalendarWidget, QListWidget, QHBoxLayout, QSpinBox,
    QTableWidget, QTableWidgetItem, QCheckBox, QHeaderView, QStackedWidget,
    QAbstractItemView, QSizePolicy
)
from PyQt5.QtGui import QFont, QPalette
from PyQt5.QtCore import Qt, QTime, QDate, pyqtSignal
from blocks import task
import copy
from datetime import timedelta, datetime
from utils import IndexStack
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QDateTimeEdit, QTextEdit, QTimeEdit, QSpinBox, QDialogButtonBox
from datetime import datetime, timedelta, date
import calendar
from collections import defaultdict

class AddTaskDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Task")
        self.resize(300, 400)

        layout = QVBoxLayout(self)

        # Name (required)
        layout.addWidget(QLabel("Task Name *"))
        self.name_input = QLineEdit()
        layout.addWidget(self.name_input)

        # Duration in minutes (required)
        layout.addWidget(QLabel("Duration (minutes) *"))
        self.duration_input = QSpinBox()
        self.duration_input.setRange(1, 1440)  # 1 minute to 24 hours
        self.duration_input.setValue(60)
        layout.addWidget(self.duration_input)

        # Deadline (required)
        layout.addWidget(QLabel("Deadline *"))
        self.deadline_input = QDateTimeEdit()
        self.deadline_input.setCalendarPopup(True)
        self.deadline_input.setDateTime(datetime.now())
        layout.addWidget(self.deadline_input)

        # Start time (optional)
        layout.addWidget(QLabel("Start Time (optional)"))
        self.start_input = QDateTimeEdit()
        self.start_input.setCalendarPopup(True)
        self.start_input.setDateTime(datetime.now())
        layout.addWidget(self.start_input)

        # Location (optional)
        layout.addWidget(QLabel("Location (optional)"))
        self.location_input = QLineEdit()
        layout.addWidget(self.location_input)

        # Notes (optional)
        layout.addWidget(QLabel("Notes (optional)"))
        self.notes_input = QTextEdit()
        layout.addWidget(self.notes_input)

        # Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(self.buttons)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

    def get_data(self):
        # Required fields
        name = self.name_input.text().strip()
        duration = timedelta(minutes=self.duration_input.value())
        deadline = self.deadline_input.dateTime().toPyDateTime()

        # Optional fields
        start = self.start_input.dateTime().toPyDateTime() if self.start_input.dateTime() != self.start_input.minimumDateTime() else None
        location = self.location_input.text().strip() or None
        notes = self.notes_input.toPlainText().strip() or None

        return {
            "name": name,
            "duration": duration,
            "deadline": deadline,
            "start": start,
            "location": location,
            "notes": notes
        }

class ScheduleView(QWidget):

    def __init__(self, schedule):
        super().__init__()
        self.schedule = schedule

        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel("Schedule View (placeholder)"))
        self.setLayout(self.layout)

class DayView(QWidget):
    back = pyqtSignal()

    def __init__(self):
        super().__init__()    

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.back_btn = QPushButton("back")
        self.back_btn.clicked.connect(self.back.emit)
        self.main_layout.addWidget(self.back_btn)

class MonthView(QWidget):
    open_settings = pyqtSignal()
    open_todo = pyqtSignal()
    open_day = pyqtSignal(object)
    back = pyqtSignal()

    def __init__(self, schedule, util):
        """
        schedule: your Schedule object containing tasks
        util: your utility object (for theme)
        """
        super().__init__()
        self.schedule = schedule
        self.util = util

        self.current_date = date.today()
        self.current_year = self.current_date.year
        self.current_month = self.current_date.month

        # Main layout
        main_layout = QVBoxLayout(self)

        top_bar, buttons = self.util.create_top_bar(
            show_back=True,
            show_todo=True,
            show_settings=True
        )

        buttons["todo"].clicked.connect(self.open_todo.emit)
        buttons["settings"].clicked.connect(self.open_settings.emit)
        buttons["back"].clicked.connect(self.back.emit)

        main_layout.addWidget(top_bar)

        # Top header: Month name and navigation
        header_layout = QHBoxLayout()
        self.prev_btn = QPushButton("<")
        self.next_btn = QPushButton(">")
        self.month_label = QLabel()
        self.month_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.prev_btn)
        header_layout.addWidget(self.month_label)
        header_layout.addWidget(self.next_btn)
        main_layout.addLayout(header_layout)

        self.prev_btn.clicked.connect(lambda: self.change_month(-1))
        self.next_btn.clicked.connect(lambda: self.change_month(1))

        # Calendar grid
        self.calendar_table = QTableWidget(6, 7)
        days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

        self.calendar_table.setHorizontalHeaderLabels(days)
        self.calendar_table.horizontalHeader().setVisible(True)

        self.calendar_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.calendar_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.calendar_table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        
        self.calendar_table.verticalHeader().setVisible(False)
        
        self.calendar_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.calendar_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.calendar_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.calendar_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Let the widget itself expand
        self.calendar_table.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
)
        main_layout.addWidget(self.calendar_table)

        self.calendar_table.cellClicked.connect(self.on_cell_clicked)

        self.refresh_month_view()
        self.util.apply_theme()

    def refresh_month_view(self):
        """Builds the 6-week calendar for the current month"""
        self.month_label.setText(f"{calendar.month_name[self.current_month].lower()} {self.current_year}")

        # Compute first day
        month_start = date(self.current_year, self.current_month, 1)
        display_start = month_start
        while display_start.strftime("%A") != "Monday":
            display_start -= timedelta(days=1)

        # Group tasks by day
        month_blocks = self.schedule.month(month_start)
        tasks_by_day = defaultdict(list)
        for block in month_blocks:
            tasks_by_day[block.start.day].append(block)

        # Get grid color from theme
        theme_name = getattr(self.util.settings, "theme", "light")
        grid_color = self.util.tm.themes.get(theme_name, {}).get("calendar_grid", "#AAAAAA")

        # Fill 6x7 grid
        for week in range(6):
            for day_col in range(7):
                cell_widget = QWidget()
                cell_layout = QVBoxLayout(cell_widget)
                cell_layout.setContentsMargins(0, 0, 0, 0)
                cell_layout.setSpacing(0)

                cell_date = display_start + timedelta(days=week*7 + day_col)
                day_number = cell_date.day
                is_current_month = (cell_date.month == self.current_month)

                # Day number
                day_label = QLabel(str(day_number))
                day_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
                day_label.setStyleSheet("font-weight: bold;" if is_current_month else "color: #AAA;")
                cell_layout.addWidget(day_label, alignment=Qt.AlignTop | Qt.AlignLeft)

                # Tasks
                if is_current_month and day_number in tasks_by_day:
                    day_tasks = tasks_by_day[day_number]
                    day_tasks.sort(key=lambda t: t.duration.total_seconds(), reverse=True)
                    for task in day_tasks[:3]:
                        task_label = QLabel(task.name)
                        task_label.setStyleSheet("font-size: 10px;")
                        task_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
                        cell_layout.addWidget(task_label)
                
                cell_layout.addStretch()

                # Store date info
                cell_widget.setProperty("is_current_month", is_current_month)
                if is_current_month:
                    cell_widget.setProperty("date", cell_date)

                # Apply grid borders directly here
                cell_widget.setStyleSheet(f"""
                    QWidget {{
                        border-top: 1px solid {grid_color};
                        border-left: 1px solid {grid_color};
                        border-bottom: 1px solid {grid_color};
                        border-right: 1px solid {grid_color};
                    }}
                """)

                self.calendar_table.setCellWidget(week, day_col, cell_widget)


    def change_month(self, delta):
        """Change the current month by delta (+1 or -1)"""
        new_month = self.current_month + delta
        new_year = self.current_year
        if new_month < 1:
            new_month = 12
            new_year -= 1
        elif new_month > 12:
            new_month = 1
            new_year += 1
        self.current_month = new_month
        self.current_year = new_year
        self.refresh_month_view()

    def on_cell_clicked(self, row, col):
        cell = self.calendar_table.cellWidget(row, col)
        if cell and cell.property("is_current_month"):
            day_date = cell.property("date")
            if day_date:
                self.open_day.emit(day_date)


class ToDoListView(QWidget):
    open_settings = pyqtSignal()
    back = pyqtSignal()

    
    def __init__(self, schedule, util, parent=None):
        super().__init__(parent)
        self.schedule = schedule
        self.show_history = False
        self.sort_state = {}  # column index -> Qt.AscendingOrder / DescendingOrder / disabled
        self.util = util
        layout = QVBoxLayout(self)
        
        top_bar, buttons = self.util.create_top_bar(
            show_back=True,
            show_settings=True
        )

        buttons["back"].clicked.connect(self.back.emit)
        buttons["settings"].clicked.connect(self.open_settings.emit)

        layout.addWidget(top_bar)


        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("search tasks by name...")
        self.search_input.textChanged.connect(self.filter_tasks)
        layout.addWidget(self.search_input)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["name", "deadline", "duration"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().sectionClicked.connect(self.handle_header_click)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

        self.toggle_btn = QPushButton("show history")
        layout.addWidget(self.toggle_btn)
        self.toggle_btn.clicked.connect(self.toggle_view)

        self.add_btn = QPushButton("add task")
        layout.addWidget(self.add_btn)
        self.add_btn.clicked.connect(self.on_add_task)

        self.util.apply_theme()

        self.refresh()

    def toggle_view(self):
        self.show_history = not self.show_history
        self.toggle_btn.setText("show to-do" if self.show_history else "show history")
        self.refresh()

    def refresh(self):
        if self.show_history:
            tasks = [t for t in self.schedule.ToDoList if t.is_completed]
            self.table.setColumnCount(4)
            self.table.setHorizontalHeaderLabels(["name", "deadline", "duration", "date completed"])
        else:
            tasks = [t for t in self.schedule.ToDoList if not t.is_completed]
            self.table.setColumnCount(4)
            self.table.setHorizontalHeaderLabels(["name", "deadline", "duration", "start time"])

        self.table.setRowCount(len(tasks))

        for row, task in enumerate(tasks):
            # Create QTableWidgetItem for sorting
            item_name = QTableWidgetItem(task.name)
            item_name.setData(Qt.UserRole, task.name.lower())  # case-insensitive sort
            self.table.setItem(row, 0, item_name)

            # Add the checkbox as cell widget
            checkbox = QCheckBox(task.name)
            checkbox.setChecked(task.is_completed)
            checkbox.stateChanged.connect(lambda state, t=task: self.on_checkbox_changed(state, t))
            self.table.setCellWidget(row, 0, checkbox)

            # Deadline
            deadline_text = task.deadline.strftime("%d/%m/%Y %H:%M") if task.deadline else "-"
            self.table.setItem(row, 1, QTableWidgetItem(deadline_text))

            # Duration in hours/minutes
            hours = task.duration.total_seconds() // 3600
            minutes = (task.duration.total_seconds() % 3600) // 60
            duration_text = f"{int(hours)}h {int(minutes)}m"
            self.table.setItem(row, 2, QTableWidgetItem(duration_text))

            # Date Completed (only for history)
            if self.show_history:
                completed_str = task.completed_at.strftime("%d/%m/%Y %H:%M") if task.completed_at else "-"
                self.table.setItem(row, 3, QTableWidgetItem(completed_str))
            else:
                start_str = task.start.strftime("%d/%m/%Y %H:%M")
                self.table.setItem(row, 3, QTableWidgetItem(start_str))

        
        self.util.apply_theme()

    def filter_tasks(self, text):
        text = text.lower()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)  # Name column
            if text in item.text().lower():
                self.table.setRowHidden(row, False)
            else:
                self.table.setRowHidden(row, True)

    def on_checkbox_changed(self, state, task):
        if state == Qt.Checked:
            self.schedule.mark_complete(task)
        else:
            self.schedule.mark_incomplete(task)
        self.refresh()

    def handle_header_click(self, col):
        state = self.sort_state.get(col, 0)

        if state == 0:
            # Ascending
            self.table.setSortingEnabled(True)
            self.table.sortItems(col, Qt.AscendingOrder)
            self.sort_state[col] = 1

        elif state == 1:
            # Descending
            self.table.sortItems(col, Qt.DescendingOrder)
            self.sort_state[col] = 2

        else:
            # Disabled → restore original order
            self.table.setSortingEnabled(False)

            header = self.table.horizontalHeader()
            header.setSortIndicator(-1, Qt.AscendingOrder)
            header.setSortIndicatorShown(False)

            self.refresh()

            self.table.setSortingEnabled(True)
            header.setSortIndicatorShown(True)

            self.sort_state[col] = 0

        # Reset all other columns
        for c in list(self.sort_state.keys()):
            if c != col:
                self.sort_state[c] = 0

    def on_add_task(self):
        dialog = AddTaskDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if not data["name"]:  # enforce name
                return
            new_task = task(
                name=data["name"],
                start=data["start"],
                duration=data["duration"],
                deadline=data["deadline"],
                location=data["location"],
                notes=data["notes"]
            )
            self.schedule.add_block(new_task)
            self.refresh()

class SettingsView(QWidget):
    back = pyqtSignal()

    def __init__(self, settings, persistence_manager, util):
        super().__init__()

        self.settings = settings
        self.persistence = persistence_manager
        self.util = util        

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        top_bar, buttons = self.util.create_top_bar(
            show_back=True
        )

        buttons["back"].clicked.connect(self.on_back_clicked)

        self.main_layout.addWidget(top_bar)


        self.general_group = QGroupBox("general settings")
        self.general_form = QFormLayout()
        self.general_group.setLayout(self.general_form)
        self.main_layout.addWidget(self.general_group)

        # Theme selection
        self.theme_box = QComboBox()
        self.theme_box.addItems(["light", "dark"])
        self.theme_box.setCurrentText(self.settings.theme)
        self.theme_box.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.theme_box.setMinimumWidth(100)
        self.general_form.addRow("theme", self.theme_box)

        # Weekday times
        self.start_time_edit = QTimeEdit(QTime(self.settings.start_time.hour, self.settings.start_time.minute))
        self.end_time_edit = QTimeEdit(QTime(self.settings.end_time.hour, self.settings.end_time.minute))
        self.general_form.addRow("weekday start time", self.start_time_edit)
        self.general_form.addRow("weekday end time", self.end_time_edit)

        self.start_time_edit.timeChanged.connect(self.validate_weekday_times)
        self.end_time_edit.timeChanged.connect(self.validate_weekday_times)


        # weekend times
        self.weekend_start_edit = QTimeEdit(QTime(self.settings.weekend_start.hour, self.settings.weekend_start.minute))
        self.weekend_end_edit = QTimeEdit(QTime(self.settings.weekend_end.hour, self.settings.weekend_end.minute))
        self.general_form.addRow("weekend start time", self.weekend_start_edit)
        self.general_form.addRow("weekend end time", self.weekend_end_edit)

        self.weekend_start_edit.timeChanged.connect(self.validate_weekend_times)
        self.weekend_end_edit.timeChanged.connect(self.validate_weekend_times)

        # break duration
        self.break_duration_spin = QSpinBox()
        self.break_duration_spin.setRange(5, 120)  # minutes
        self.break_duration_spin.setSuffix(" min")
        self.break_duration_spin.setValue(int(self.settings.break_duration.total_seconds() // 60))
        self.break_duration_spin.valueChanged.connect(self.on_break_duration_changed)
        self.general_form.addRow("break duration", self.break_duration_spin)

        # notification
        self.notification_spin = QSpinBox()
        self.notification_spin.setRange(1, 120)  # minutes
        self.notification_spin.setSuffix(" min")
        self.notification_spin.setValue(int(self.settings.notification_frequency.total_seconds() // 60))
        self.notification_spin.valueChanged.connect(self.on_notification_duration_changed)
        self.general_form.addRow("notification duration", self.notification_spin)

        # meal times
        self.meal_group = QGroupBox("meal times")
        self.meal_form = QFormLayout()
        self.meal_group.setLayout(self.meal_form)
        self.main_layout.addWidget(self.meal_group)

        self.meal_edits = {}
        for meal, (start, end) in self.settings.meal_windows.items():
            start_edit = QTimeEdit(QTime(start.hour, start.minute))
            end_edit = QTimeEdit(QTime(end.hour, end.minute))
            start_edit.timeChanged.connect(self.validate_meal_times)
            end_edit.timeChanged.connect(self.validate_meal_times)
            self.meal_form.addRow(f"{meal} start".lower(), start_edit)
            self.meal_form.addRow(f"{meal} end".lower(), end_edit)
            self.meal_edits[meal] = (start_edit, end_edit)

        # holidays
        self.holiday_group = QGroupBox("holidays (max 3)")
        self.holiday_layout = QVBoxLayout()
        self.holiday_layout.setContentsMargins(6, 20, 6, 6)  # top margin ensures title is visible
        self.holiday_layout.addSpacing(6)
        self.holiday_group.setLayout(self.holiday_layout)
        self.main_layout.addWidget(self.holiday_group)

        # Holiday list
        self.holiday_list_widget = QListWidget()
        self.holiday_list_widget.itemDoubleClicked.connect(self.edit_holiday)
        self.holiday_layout.addWidget(self.holiday_list_widget)

        # Buttons
        btn_layout = QHBoxLayout()
        self.add_holiday_btn = QPushButton("add holiday")
        self.remove_holiday_btn = QPushButton("remove selected")
        self.add_holiday_btn.clicked.connect(self.add_holiday)
        self.remove_holiday_btn.clicked.connect(self.remove_selected_holiday)
        btn_layout.addWidget(self.add_holiday_btn)
        btn_layout.addWidget(self.remove_holiday_btn)
        self.holiday_layout.addLayout(btn_layout)

        # Snapshot
        self._snapshot = self._snapshot_state()
        self._temp_state = copy.deepcopy(self._snapshot)

        self.refresh_holiday_list()



        # save button
        self.save_btn = QPushButton("save settings")
        self.save_btn.clicked.connect(self.save_settings)
        self.main_layout.addWidget(self.save_btn)

        # headder fonts
        self.header_font = QFont()
        self.header_font.setPointSize(16)
        for group in [self.general_group, self.meal_group, self.holiday_group]:
            group.setFont(self.header_font)


        self.save_btn.setEnabled(False)
        # connect theme change
        self.theme_box.currentTextChanged.connect(self.on_theme_changed)

        # apply theme initially
        self.util.apply_theme()

    
    # state snapshot
    def _snapshot_state(self):
        return {
            "theme": self.theme_box.currentText(),
            "weekday_start": self.start_time_edit.time().toString("HH:mm"),
            "weekday_end": self.end_time_edit.time().toString("HH:mm"),
            "weekend_start": self.weekend_start_edit.time().toString("HH:mm"),
            "weekend_end": self.weekend_end_edit.time().toString("HH:mm"),
            "break_duration": self.break_duration_spin.value(),
            "notification_frequency": self.notification_spin.value(),
            "meal_windows": {
                meal: (
                    start.time().toString("HH:mm"),
                    end.time().toString("HH:mm")
                )
                for meal, (start, end) in self.meal_edits.items()
            },
            "holidays": list(self.settings.holiday_ranges)
        }  

    # save logic
    def _is_dirty(self):
        return self._temp_state != self._snapshot
    
    def _update_save_state(self):
        self.save_btn.setEnabled(self._is_dirty())
    
    def save_settings(self, skip_confirmation=False):
        if not self._is_dirty():
            return

        if not skip_confirmation:
            reply = QMessageBox.question(
                self,
                "Confirm Save",
                "Do you want to save your settings?",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply != QMessageBox.Yes:
                return

        # actually save
        self.settings.theme = self._temp_state["theme"]
        self.settings.start_time = QTime.fromString(self._temp_state["weekday_start"], "HH:mm").toPyTime()
        self.settings.end_time = QTime.fromString(self._temp_state["weekday_end"], "HH:mm").toPyTime()
        self.settings.weekend_start = QTime.fromString(self._temp_state["weekend_start"], "HH:mm").toPyTime()
        self.settings.weekend_end = QTime.fromString(self._temp_state["weekend_end"], "HH:mm").toPyTime()
        self.settings.break_duration = timedelta(minutes=self._temp_state["break_duration"])
        self.settings.notification_frequency = timedelta(minutes=self._temp_state["notification_frequency"])

        for meal, (s, e) in self._temp_state["meal_windows"].items():
            self.settings.meal_windows[meal] = (
                QTime.fromString(s, "HH:mm").toPyTime(),
                QTime.fromString(e, "HH:mm").toPyTime()
            )

        self.settings.holiday_ranges = list(self._temp_state["holidays"])
        self.persistence.save_settings(self.settings)

        self._snapshot = copy.deepcopy(self._temp_state)
        self._update_save_state()

    def closeEvent(self, event):
        if self._is_dirty():
            reply = QMessageBox.question(
                self,
                "unsaved changes",
                "you have unsaved changes. do you want to save before exiting?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )

            if reply == QMessageBox.Yes:
                self.save_settings(True)
                event.accept()
            elif reply == QMessageBox.No:
                event.accept()
            else:  # Cancel
                event.ignore()
        else:
            event.accept()

    def on_break_duration_changed(self, value):
        self._temp_state["break_duration"] = value
        self._update_save_state()

    def on_notification_duration_changed(self, value):
        self._temp_state["notification_frequency"] = value
        self._update_save_state()
 
    def on_back_clicked(self):
        if self._is_dirty():
            reply = QMessageBox.question(
                self,
                "unsaved changes",
                "you have unsaved changes. do you want to save before going back?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )

            if reply == QMessageBox.Yes:
                self.save_settings(True)
                self.back.emit()
            elif reply == QMessageBox.No:
                self.back.emit()
            else:  # Cancel
                pass  # do nothing, stay on settings
        else:
            self.back.emit()
        
    # holidays
    def add_holiday(self):
        if len(self._temp_state["holidays"]) >= 3:
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

        if start_date > end_date: # invalid range
            QMessageBox.warning(self, "invalid range", "start date cannot be after end date.")
            return

        if len(self.settings.holiday_ranges) >= 3: # no more than 3 holidays
            QMessageBox.warning(self, "max holidays", "you can only have up to 3 holidays.")
            return

        self._temp_state["holidays"].append((start_date, end_date))
        self.refresh_holiday_list()
        self._update_save_state()

    def edit_holiday(self, item):   
        index = self.holiday_list_widget.row(item)
        start, end = self._temp_state["holidays"][index]

        dialog = QDialog(self)
        dialog.setWindowTitle("edit holiday")
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

        # Update the holiday in temp
        self._temp_state["holidays"][index] = (start_date, end_date)
        self._update_save_state()
        self.refresh_holiday_list()
        dialog.accept()

    def remove_selected_holiday(self):
        selected_items = self.holiday_list_widget.selectedItems()
        if not selected_items:
            return
        for item in selected_items:
            index = self.holiday_list_widget.row(item)
            del self._temp_state["holidays"][index]
            self._update_save_state()
        self.refresh_holiday_list()

    def refresh_holiday_list(self):
        self.holiday_list_widget.clear()
        for start, end in self._temp_state["holidays"]:
            self.holiday_list_widget.addItem(f"{start} → {end}")

    #time validation
    def validate_weekday_times(self):
        start = self.start_time_edit.time()
        end = self.end_time_edit.time()
        

        if start >= end or start.addSecs(10 * 60 * 60) > end:
            t = self._temp_state
            self.start_time_edit.setTime(QTime.fromString(t["weekday_start"], "HH:mm"))
            self.end_time_edit.setTime(QTime.fromString(t["weekday_end"], "HH:mm"))
            return
        
        self.enforce_breakfast_rule()

        start = self.util.round_to_5(start)
        end = self.util.round_to_5(end)

        self._temp_state["weekday_start"] = start.toString("HH:mm")
        self._temp_state["weekday_end"] = end.toString("HH:mm")
        self._update_save_state()
        
    def validate_weekend_times(self):
        start = self.weekend_start_edit.time()
        end = self.weekend_end_edit.time()

        if start >= end or start.addSecs(10 * 60 * 60) > end:
            t = self._temp_state
            self.weekend_start_edit.setTime(QTime.fromString(t["weekend_start"], "HH:mm"))
            self.weekend_end_edit.setTime(QTime.fromString(t["weekend_end"], "HH:mm"))
            return
        
        self.enforce_breakfast_rule()

        start = self.util.round_to_5(start)
        end = self.util.round_to_5(end)

        self._temp_state["weekend_start"] = start.toString("HH:mm")
        self._temp_state["weekend_end"] = end.toString("HH:mm")
        self._update_save_state()

    def enforce_breakfast_rule(self):
        """Ensure breakfast ends at least 30 mins after day start."""
        b_start_edit, b_end_edit = self.meal_edits["breakfast"]

        latest_day_start = max(
            self.start_time_edit.time(),
            self.weekend_start_edit.time()
        )

        if b_end_edit.time() < latest_day_start.addSecs(30*60):
            # reset breakfast to previous valid times
            ts, te = self._temp_state["meal_windows"]["breakfast"]
            b_start_edit.setTime(QTime.fromString(ts, "HH:mm"))
            b_end_edit.setTime(QTime.fromString(te, "HH:mm"))
            # update temp state just in case
            self._temp_state["meal_windows"]["breakfast"] = (ts, te)
            self._update_save_state()

    def validate_meal_times(self):
        meals = {
            meal: (start.time(), end.time())
            for meal, (start, end) in self.meal_edits.items()
        }

        # start < end
        for meal, (start, end) in meals.items():
            if start >= end:
                ts, te = self._temp_state["meal_windows"][meal]
                s, e = self.meal_edits[meal]
                s.setTime(QTime.fromString(ts, "HH:mm"))
                e.setTime(QTime.fromString(te, "HH:mm"))
                return
            
        #minimum 30 mins
        for meal, (start, end) in meals.items():
            if start.addSecs(30 * 60) > end:
                ts, te = self._temp_state["meal_windows"][meal]
                s, e = self.meal_edits[meal]
                s.setTime(QTime.fromString(ts, "HH:mm"))
                e.setTime(QTime.fromString(te, "HH:mm"))
                return

        # breakfast rule
        b_start, b_end = meals["breakfast"]
        latest_day_start = max(
            self.start_time_edit.time(),
            self.weekend_start_edit.time()
        )
        if b_end < latest_day_start.addSecs(30 * 60):
            ts, te = self._temp_state["meal_windows"]["breakfast"]
            s, e = self.meal_edits["breakfast"]
            s.setTime(QTime.fromString(ts, "HH:mm"))
            e.setTime(QTime.fromString(te, "HH:mm"))
            return

        # no overlap
        for m1, (s1, e1) in meals.items():
            for m2, (s2, e2) in meals.items():
                if m1 != m2 and s1 < e2 and e1 > s2:
                    ts, te = self._temp_state["meal_windows"][m1]
                    s, e = self.meal_edits[m1]
                    s.setTime(QTime.fromString(ts, "HH:mm"))
                    e.setTime(QTime.fromString(te, "HH:mm"))
                    return

        # VALID → commit to temp
        for meal, (start, end) in meals.items():
            self._temp_state["meal_windows"][meal] = (
                self.util.round_to_5(start).toString("HH:mm"),
                self.util.round_to_5(end).toString("HH:mm")
            )

        self._update_save_state()

    # theme application
    def on_theme_changed(self):
        self._temp_state["theme"] = self.theme_box.currentText()
        self.util.apply_theme(self._temp_state["theme"])
        self._update_save_state()


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
        self.day_view = DayView()

        self.stack.addWidget(self.month_view)
        self.stack.addWidget(self.settings_view)
        self.stack.addWidget(self.todo_view)
        self.stack.addWidget(self.day_view)

        # Navigation
        self.todo_view.open_settings.connect(lambda: self.switch_to(1))
        self.todo_view.back.connect(lambda: self.switch_back())
        self.settings_view.back.connect(lambda: self.switch_back())
        self.month_view.open_settings.connect(lambda: self.switch_to(1))
        self.month_view.open_todo.connect(lambda: self.switch_to(2))
        self.month_view.open_day.connect(lambda: self.switch_to(3))
        self.month_view.back.connect(lambda: self.switch_back())
        self.day_view.back.connect(lambda: self.switch_back())



        # Apply themes
        self.util.apply_theme()

    def switch_to(self, index):
        if index != self.current_index:
            self.index_stack.add_item(self.current_index)
        self.stack.setCurrentIndex(index)
        self.current_index = index


    def switch_back(self):
        popped = self.index_stack.pop_item()
        if popped is None:
            QMessageBox.warning(self, "oopsie woopsie", "cannot go back anymore")
        else:
            self.stack.setCurrentIndex(popped)
            self.current_index = popped

