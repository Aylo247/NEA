from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QCheckBox, QHeaderView, 
    QAbstractItemView, QSizePolicy, QLineEdit, QDialog
)
from PyQt5.QtCore import (
    Qt, pyqtSignal
)
from blocks import task
import calendar
from collections import defaultdict
from datetime import timedelta, date
from dialogs import AddTaskDialog

class MonthView(QWidget):
    open_settings = pyqtSignal()
    open_todo = pyqtSignal()
    open_day = pyqtSignal(object)
    back = pyqtSignal()

    def __init__(self, schedule, util):
        super().__init__()
        self.schedule = schedule
        self.util = util

        self.current_date = date.today()
        self.current_year = self.current_date.year
        self.current_month = self.current_date.month

        # Main layout
        main_layout = QVBoxLayout(self)

        # Top bar (back, todo, settings)
        top_bar, buttons = self.util.create_top_bar(
            show_back=True, show_todo=True, show_settings=True
        )
        buttons["back"].clicked.connect(self.back.emit)
        buttons["todo"].clicked.connect(self.open_todo.emit)
        buttons["settings"].clicked.connect(self.open_settings.emit)
        main_layout.addWidget(top_bar)

        # Month navigation header
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
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        self.calendar_table.setHorizontalHeaderLabels(days)
        self.calendar_table.horizontalHeader().setVisible(True)
        self.calendar_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.calendar_table.verticalHeader().setVisible(False)
        self.calendar_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.calendar_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.calendar_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.calendar_table.cellClicked.connect(self.on_cell_clicked)
        self.calendar_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.calendar_table)

        self.refresh_month_view()
        self.util.apply_theme()

    def refresh_month_view(self):
        """Populate the 6x7 calendar grid for the current month."""
        self.month_label.setText(f"{calendar.month_name[self.current_month]} {self.current_year}")

        # Start display from the Monday of the week containing the 1st
        month_start = date(self.current_year, self.current_month, 1)
        display_start = month_start
        while display_start.weekday() != 0:  # 0 = Monday
            display_start -= timedelta(days=1)

        # Get tasks for the current month
        month_blocks = self.schedule.month(month_start)
        tasks_by_day = defaultdict(list)
        for block in month_blocks:
            tasks_by_day[block.start.date()].append(block)

        # Grid color from theme
        theme_name = getattr(self.util.settings, "theme", "light")
        grid_color = self.util.tm.themes.get(theme_name, {}).get("calendar_grid", "#AAAAAA")

        # Populate cells
        for week in range(6):
            for day_col in range(7):
                cell_date = display_start + timedelta(days=week*7 + day_col)
                is_current_month = (cell_date.month == self.current_month)

                cell_widget = QWidget()
                cell_layout = QVBoxLayout(cell_widget)
                cell_layout.setContentsMargins(2, 2, 2, 2)
                cell_layout.setSpacing(0)

                # Day number
                day_label = QLabel(str(cell_date.day))
                day_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
                day_label.setStyleSheet(
                    "font-weight: bold;" if is_current_month else "color: #AAA;"
                )
                cell_layout.addWidget(day_label)

                # Tasks (only show for actual month, optional)
                day_tasks = tasks_by_day.get(cell_date, [])
                day_tasks.sort(key=lambda t: t.duration.total_seconds(), reverse=True)
                for task in day_tasks[:3]:
                    task_label = QLabel(task.name)
                    task_label.setStyleSheet("font-size: 10px;")
                    task_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
                    cell_layout.addWidget(task_label)

                cell_layout.addStretch()

                # Store date info for all cells
                cell_widget.setProperty("date", cell_date)
                cell_widget.setProperty("is_current_month", is_current_month)

                # Apply cell borders
                cell_widget.setStyleSheet(f"""
                    QWidget {{
                        border: 1px solid {grid_color};
                    }}
                """)

                self.calendar_table.setCellWidget(week, day_col, cell_widget)

    def change_month(self, delta):
        """Change the current month by delta (+1 or -1)."""
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
        """Emit the date for the clicked cell, even if out-of-month."""
        cell = self.calendar_table.cellWidget(row, col)
        if cell:
            day_date = cell.property("date")
            if day_date:
                print(f"Clicked on date: {day_date}")
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
            self.table.setColumnCount(5)
            self.table.setHorizontalHeaderLabels(["Done", "Name", "Deadline", "Duration", "Date Completed"])
        else:
            tasks = [t for t in self.schedule.ToDoList if not t.is_completed]
            self.table.setColumnCount(5)
            self.table.setHorizontalHeaderLabels(["Done", "Name", "Deadline", "Duration", "Start Time"])

        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 40)  # width just enough for checkbox

        # Make the rest of the columns stretch equally
        for col in range(1, self.table.columnCount()):
            self.table.horizontalHeader().setSectionResizeMode(col, QHeaderView.Stretch)

        self.table.setRowCount(len(tasks))

        for row, task in enumerate(tasks):
            # Column 0: checkbox
            checkbox = QCheckBox()
            checkbox.setChecked(task.is_completed)
            checkbox.stateChanged.connect(lambda state, t=task: self.on_checkbox_changed(state, t))
            self.table.setCellWidget(row, 0, checkbox)

            # Column 1: task name
            name_item = QTableWidgetItem(task.name)
            self.table.setItem(row, 1, name_item)

            # Column 2: Deadline
            deadline_text = task.deadline.strftime("%d/%m/%Y %H:%M") if task.deadline else "-"
            self.table.setItem(row, 2, QTableWidgetItem(deadline_text))

            # Column 3: Duration
            hours = task.duration.total_seconds() // 3600
            minutes = (task.duration.total_seconds() % 3600) // 60
            duration_text = f"{int(hours)}h {int(minutes)}m"
            self.table.setItem(row, 3, QTableWidgetItem(duration_text))

            # Column 4: Start/Completed
            if self.show_history:
                completed_str = task.completed_at.strftime("%d/%m/%Y %H:%M") if task.completed_at else "-"
                self.table.setItem(row, 4, QTableWidgetItem(completed_str))
            else:
                start_str = task.start.strftime("%d/%m/%Y %H:%M")
                self.table.setItem(row, 4, QTableWidgetItem(start_str))
        


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
        dialog = AddTaskDialog(utils=self.util, parent=self)
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

        