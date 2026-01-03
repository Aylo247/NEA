from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QCheckBox, QHeaderView, 
    QAbstractItemView, QSizePolicy, QLineEdit, QDialog,
    QStyledItemDelegate
)
from PyQt5.QtCore import Qt, pyqtSignal, QRect
from PyQt5.QtGui import QColor, QPalette
from blocks import Task
from dialogs import AddTaskDialog
import calendar
from collections import defaultdict
from datetime import date, timedelta


class VerticalHeaderDelegate(QStyledItemDelegate):
    """custom delegate to render vertical text in table headers"""
    
    def paint(self, painter, option, index) -> None:
        painter.save()
        text = index.data(Qt.DisplayRole)

        # swap width/height for rotated text
        text_rect_width = option.rect.height()
        text_rect_height = option.rect.width()
        new_rect = QRect(0, 0, text_rect_width, text_rect_height)

        # move and rotate painter
        painter.translate(option.rect.x(), option.rect.y() + option.rect.height())
        painter.rotate(-90)

        # draw centered text
        painter.drawText(new_rect, Qt.AlignCenter, text)
        painter.restore()


class MonthView(QWidget):
    """month view calendar showing tasks and week labels"""
    
    open_settings = pyqtSignal()
    open_todo = pyqtSignal()
    open_day = pyqtSignal(object)  # emits a date object
    back = pyqtSignal()
    open_week = pyqtSignal(object)  # emits week start date

    def __init__(self, schedule, util) -> None:
        """initialize MonthView with calendar table and navigation"""
        super().__init__()
        self.schedule = schedule
        self.util = util
        self.current_date = date.today()
        self.current_year = self.current_date.year
        self.current_month = self.current_date.month

        # main layout
        main_layout = QVBoxLayout(self)

        # top bar (back, todo, settings)
        top_bar, buttons = self.util.create_top_bar(
            show_back=True, show_todo=True, show_settings=True
        )
        buttons["back"].clicked.connect(self.back.emit)
        buttons["todo"].clicked.connect(self.open_todo.emit)
        buttons["settings"].clicked.connect(self.open_settings.emit)
        main_layout.addWidget(top_bar)

        # month navigation header
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
        self.calendar_table = QTableWidget(6, 8)
        days = ["", "mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        self.calendar_table.setHorizontalHeaderLabels(days)
        self.calendar_table.horizontalHeader().setVisible(True)
        self.calendar_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.calendar_table.verticalHeader().setVisible(False)
        self.calendar_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.calendar_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.calendar_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.calendar_table.cellClicked.connect(self.on_cell_clicked)
        self.calendar_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        delegate = VerticalHeaderDelegate(self.calendar_table)
        self.calendar_table.setItemDelegateForColumn(0, delegate)
        self.calendar_table.setColumnWidth(0, 10)
        self.calendar_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        main_layout.addWidget(self.calendar_table)

        self.refresh_month_view()
        self.util.apply_theme()

    def refresh_month_view(self) -> None:
        """populate the 6x7 calendar grid for the current month with tasks"""
        self.month_label.setText(f"{calendar.month_name[self.current_month]} {self.current_year}")

        # find monday of first week to display
        month_start = date(self.current_year, self.current_month, 1)
        display_start = month_start
        while display_start.weekday() != 0:
            display_start -= timedelta(days=1)

        # collect Tasks by day
        month_blocks = self.schedule.month(month_start)
        tasks_by_day = defaultdict(list)
        for block in month_blocks:
            tasks_by_day[block.start.date()].append(block)

        # fill table

        today = date.today()
        IGNORE_TASKS = {"breakfast", "lunch", "dinner", "break"}

        for week in range(6):
            week_start = display_start + timedelta(days=week * 7)
            wc_item = QTableWidgetItem(f"WC {week_start.strftime('%d/%m')}")
            wc_item.setTextAlignment(Qt.AlignCenter)
            wc_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            wc_item.setData(Qt.UserRole, week_start)
            self.calendar_table.setItem(week, 0, wc_item)


            for day_col in range(1, 8):
                cell_date = display_start + timedelta(days=week * 7 + day_col - 1)

                is_current_month = (cell_date.month == self.current_month)
                is_today = (cell_date == today)

                cell_widget = QWidget()
                cell_layout = QVBoxLayout(cell_widget)
                cell_layout.setContentsMargins(4, 4, 4, 4)
                cell_layout.setSpacing(1)


                # --- day number ---
                day_label = QLabel(str(cell_date.day))
                day_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)

                if is_current_month:
                    day_label.setStyleSheet("font-weight: bold;")
                else:
                    day_label.setStyleSheet("color: #AAA;")

                cell_layout.addWidget(day_label)

                # --- tasks (filtered) ---
                day_tasks = tasks_by_day.get(cell_date, [])
                filtered_tasks = [
                    t for t in day_tasks
                    if t.name.strip().lower() not in IGNORE_TASKS
                ]

                filtered_tasks.sort(
                    key=lambda t: t.duration.total_seconds(),
                    reverse=True
                )

                for t in filtered_tasks[:3]:
                    t_label = QLabel(t.name)
                    t_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
                    t_label.setStyleSheet("font-size: 10px;")
                    cell_layout.addWidget(t_label)

                cell_layout.addStretch()

                cell_widget.setProperty("date", cell_date)
                cell_widget.setProperty("is_current_month", is_current_month)
                self.calendar_table.setCellWidget(week, day_col, cell_widget)



    def change_month(self, delta: int) -> None:
        """change the current month by delta (+1 or -1)"""
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

    def change_to_month(self, month: int, year: int) -> None:
        """directly switch to a specific month/year"""
        self.current_month = month
        self.current_year = year
        self.refresh_month_view()

    def on_cell_clicked(self, row: int, col: int) -> None:
        """emit date for clicked cell: day or week start"""
        if col == 0:  # week start column
            item = self.calendar_table.item(row, col)
            if item:
                week_start = item.data(Qt.UserRole)
                if week_start:
                    self.open_week.emit(week_start)
        else:  # day cell
            cell = self.calendar_table.cellWidget(row, col)
            if cell:
                day_date = cell.property("date")
                if day_date:
                    self.open_day.emit(day_date)


class ToDoListView(QWidget):
    """view for displaying and managing the to-do list, including completed history"""
    
    open_settings = pyqtSignal()
    back = pyqtSignal()

    def __init__(self, schedule, util, parent=None) -> None:
        """initialize the ToDoListView with table, search, toggle, and add buttons"""
        super().__init__(parent)
        self.schedule = schedule
        self.util = util
        self.show_history: bool = False
        self.sort_state: dict[int, int] = {}  # column -> sort state
        layout = QVBoxLayout(self)

        # top bar
        top_bar, buttons = self.util.create_top_bar(show_back=True, show_settings=True)
        buttons["back"].clicked.connect(self.back.emit)
        buttons["settings"].clicked.connect(self.open_settings.emit)
        layout.addWidget(top_bar)

        # search field
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("search tasks by name...")
        self.search_input.textChanged.connect(self.filter_tasks)
        layout.addWidget(self.search_input)

        # table
        self.table = QTableWidget()
        self.table.setColumnCount(3)  # placeholder
        self.table.setHorizontalHeaderLabels(["name", "deadline", "duration"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().sectionClicked.connect(self.handle_header_click)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

        # toggle history button
        self.toggle_btn = QPushButton("show history")
        self.toggle_btn.clicked.connect(self.toggle_view)
        layout.addWidget(self.toggle_btn)

        # add task button
        self.add_btn = QPushButton("add task")
        self.add_btn.clicked.connect(self.on_add_task)
        layout.addWidget(self.add_btn)

        self.util.apply_theme()
        self.refresh()

    def toggle_view(self) -> None:
        """switch between showing active tasks and completed history"""
        self.show_history = not self.show_history
        self.toggle_btn.setText("show to-do" if self.show_history else "show history")
        self.refresh()

    def refresh(self) -> None:
        """populate table with tasks, checkboxes, deadlines, durations, and start/completion times."""
        if self.show_history:
            tasks = [t for t in self.schedule.ToDoList if t.is_completed]
            self.table.setColumnCount(5)
            self.table.setHorizontalHeaderLabels(["done", "name", "deadline", "duration", "date completed"])
        else:
            tasks = [t for t in self.schedule.ToDoList if not t.is_completed]
            self.table.setColumnCount(5)
            self.table.setHorizontalHeaderLabels(["done", "name", "deadline", "duration", "start time"])

        # first column fixed width
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 40)

        # rest stretch
        for col in range(1, self.table.columnCount()):
            self.table.horizontalHeader().setSectionResizeMode(col, QHeaderView.Stretch)

        self.table.setRowCount(len(tasks))

        for row, t in enumerate(tasks):
            # checkbox
            cb = QCheckBox()
            cb.setChecked(t.is_completed)
            cb.stateChanged.connect(lambda state, task=t: self.on_checkbox_changed(state, task))
            self.table.setCellWidget(row, 0, cb)

            # Name
            self.table.setItem(row, 1, QTableWidgetItem(t.name))

            # deadline
            deadline_text = t.deadline.strftime("%d/%m/%Y %H:%M") if t.deadline else "-"
            self.table.setItem(row, 2, QTableWidgetItem(deadline_text))

            # duration
            hours = t.duration.total_seconds() // 3600
            minutes = (t.duration.total_seconds() % 3600) // 60
            self.table.setItem(row, 3, QTableWidgetItem(f"{int(hours)}h {int(minutes)}m"))

            # start / completed
            if self.show_history:
                completed_str = t.completed_at.strftime("%d/%m/%Y %H:%M") if t.completed_at else "-"
                self.table.setItem(row, 4, QTableWidgetItem(completed_str))
            else:
                start_str = t.start.strftime("%d/%m/%Y %H:%M")
                self.table.setItem(row, 4, QTableWidgetItem(start_str))

        self.util.apply_theme()

    def filter_tasks(self, text: str) -> None:
        """filter rows in table based on search input"""
        text = text.lower()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 1)  # name column
            self.table.setRowHidden(row, text not in item.text().lower())

    def on_checkbox_changed(self, state: int, task) -> None:
        """handle checkbox state change for marking complete/incomplete"""
        if state == Qt.Checked:
            self.schedule.mark_complete(task)
        else:
            self.schedule.mark_incomplete(task)
        self.refresh()

    def handle_header_click(self, col: int) -> None:
        """sort table column or restore original order on multiple clicks"""
        state = self.sort_state.get(col, 0)

        if state == 0:
            self.table.setSortingEnabled(True)
            self.table.sortItems(col, Qt.AscendingOrder)
            self.sort_state[col] = 1
        elif state == 1:
            self.table.sortItems(col, Qt.DescendingOrder)
            self.sort_state[col] = 2
        else:
            self.table.setSortingEnabled(False)
            header = self.table.horizontalHeader()
            header.setSortIndicator(-1, Qt.AscendingOrder)
            header.setSortIndicatorShown(False)
            self.refresh()
            self.table.setSortingEnabled(True)
            header.setSortIndicatorShown(True)
            self.sort_state[col] = 0

        # reset other columns
        for c in list(self.sort_state.keys()):
            if c != col:
                self.sort_state[c] = 0

    def on_add_task(self) -> None:
        """open dialog to add a new task and refresh table if accepted"""
        dialog = AddTaskDialog(utils=self.util, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if not data["name"]:
                return
            new_task = Task(
                name=data["name"],
                start=data["start"],
                duration=data["duration"],
                deadline=data["deadline"],
                location=data["location"],
                notes=data["notes"]
            )
            self.schedule.add_block(new_task)
            self.refresh()
