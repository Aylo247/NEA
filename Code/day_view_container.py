from PyQt5.QtWidgets import (
   QWidget, QVBoxLayout, QScrollArea,
   QHBoxLayout,QPushButton, QLabel
)
from PyQt5.QtCore import Qt, pyqtSignal
from datetime import timedelta
from day_view import DayView
from block_pool import BlockPool


class DayViewScroll(QScrollArea):
    def __init__(self, day_view):
        super().__init__()
        self.setWidgetResizable(True)
        self.setWidget(day_view)
        self.viewport().setAcceptDrops(True)

    def dragEnterEvent(self, event):
        self.widget().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        self.widget().dragMoveEvent(event)

    def dropEvent(self, event):
        # Map viewport coords → DayView coords
        mapped_pos = self.widget().mapFrom(
            self.viewport(), event.pos()
        )
        event.setDropAction(Qt.CopyAction)
        event.accept()

        # Fake a new event with mapped coords
        event._mapped_pos = mapped_pos
        self.widget().dropEvent(event)

class DayViewContainer(QWidget):
    open_settings = pyqtSignal()
    open_todo = pyqtSignal()
    back = pyqtSignal()
    open_month = pyqtSignal()
    def __init__(self, schedule, utils):
        super().__init__()

        self.setWindowTitle("DayView with Draggable Blocks")
        main_layout = QVBoxLayout(self)  # vertical layout to stack header + content
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- HEADER ---
        header_bar, buttons = utils.create_top_bar(
            show_back=True, show_settings=True, show_todo=True, show_month=True
        )
        main_layout.addWidget(header_bar)

        day_header_layout = QHBoxLayout()
        self.prev_day_btn = QPushButton("<")
        self.next_day_btn = QPushButton(">")
        self.day_label = QLabel()
        self.day_label.setAlignment(Qt.AlignCenter)
        day_header_layout.addWidget(self.prev_day_btn)
        day_header_layout.addWidget(self.day_label)
        day_header_layout.addWidget(self.next_day_btn)
        main_layout.addLayout(day_header_layout)


        # --- Connect buttons ---
        self.prev_day_btn.clicked.connect(self.go_to_prev_day)
        self.next_day_btn.clicked.connect(self.go_to_next_day)

        # --- Connect buttons ---
        if "back" in buttons:
            buttons["back"].clicked.connect(self.back.emit)
        if "settings" in buttons:
            buttons["settings"].clicked.connect(self.open_settings.emit)
        if "todo" in buttons:
            buttons["todo"].clicked.connect(self.open_todo.emit)
        if "month" in buttons:
            buttons["month"].clicked.connect(self.open_month.emit)

        layout = QHBoxLayout(self)

        # Left: DayView with scroll
        self.day_view = DayView(schedule, utils)
        scroll = DayViewScroll(self.day_view)
        scroll.setAcceptDrops(True)
        scroll.viewport().setAcceptDrops(True)
        layout.addWidget(scroll, 3)

        self.update_day_label()

        # Right: BlockPool
        self.block_pool = BlockPool(self.day_view)
        layout.addWidget(self.block_pool, 1)
        main_layout.addLayout(layout)

    def set_current_day(self, day_date):
        self.day_view.set_current_day(day_date)
        self.update_day_label()

    def update_day_label(self):
        self.day_label.setText(self.day_view.current_day.strftime("%A, %d %B %Y"))

    def go_to_prev_day(self):
        if self.day_view.current_day:
            self.day_view.set_current_day(self.day_view.current_day - timedelta(days=1))
            self.update_day_label()

    def go_to_next_day(self):
        if self.day_view.current_day:
            self.day_view.set_current_day(self.day_view.current_day + timedelta(days=1))
            self.update_day_label()
