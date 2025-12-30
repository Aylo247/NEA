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
        self.day_view = day_view

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-block"):
            event.acceptProposedAction()
            data = eval(event.mimeData().data("application/x-block").data().decode())
            # mark incoming block from pool or another DayView
            self.day_view.incoming_block = data.copy()
            self.day_view.update()

    def dragMoveEvent(self, event):
        self.day_view.dragMoveEvent(event)

    def dropEvent(self, event):
        if not event.mimeData().hasFormat("application/x-block"):
            return

        # Map coordinates from viewport → DayView
        mapped_pos = self.day_view.mapFrom(self.viewport(), event.pos())
        event._mapped_pos = mapped_pos

        # Set CopyAction
        event.setDropAction(Qt.CopyAction)
        event.accept()

        # Delegate drop to DayView
        self.day_view.dropEvent(event)

        # Clear ghost/incoming block
        self.day_view.incoming_block = None


class DayViewContainer(QWidget):
    open_settings = pyqtSignal()
    open_todo = pyqtSignal()
    back = pyqtSignal()
    open_month = pyqtSignal(object, object)
    open_week = pyqtSignal(object)
    def __init__(self, schedule, utils, customs):
        super().__init__()

        self.setWindowTitle("DayView with Draggable Blocks")
        # --- Main vertical layout ---
        main_layout = QVBoxLayout(self)  # layout for header + content
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- HEADER ---
        header_bar, buttons = utils.create_top_bar(
            show_back=True, show_settings=True, show_todo=True, 
            show_month=True, show_week = True
        )
        main_layout.addWidget(header_bar)

        # --- Connect header buttons ---
        if "back" in buttons:
            buttons["back"].clicked.connect(self.back.emit)
        if "settings" in buttons:
            buttons["settings"].clicked.connect(self.open_settings.emit)
        if "todo" in buttons:
            buttons["todo"].clicked.connect(self.open_todo.emit)
        if "month" in buttons:
            buttons["month"].clicked.connect(self.open_month_view)
        if "week" in buttons:
            buttons["week"].clicked.connect(self.open_week_view)

        day_header_layout = QHBoxLayout()
        self.prev_day_btn = QPushButton("<")
        self.next_day_btn = QPushButton(">")
        self.day_label = QLabel()
        self.day_label.setAlignment(Qt.AlignCenter)
        day_header_layout.addWidget(self.prev_day_btn)
        day_header_layout.addWidget(self.day_label)
        day_header_layout.addWidget(self.next_day_btn)
        main_layout.addLayout(day_header_layout)

        # --- Connect day navigation ---
        self.prev_day_btn.clicked.connect(self.go_to_prev_day)
        self.next_day_btn.clicked.connect(self.go_to_next_day)

        # --- CONTENT ---
        content_layout = QHBoxLayout()  # nested layout for DayView + BlockPool

        # Left: DayView with scroll
        self.day_view = DayView(schedule, utils, customs)
        scroll = DayViewScroll(self.day_view)
        scroll.setAcceptDrops(True)
        scroll.viewport().setAcceptDrops(True)
        content_layout.addWidget(scroll, 3)

        # --- Right: BlockPool + Button ---
        right_layout = QVBoxLayout()
        self.block_pool = BlockPool(self.day_view, customs)
        right_layout.addWidget(self.block_pool)

        # Add the "New Custom Block" button below the list
        self.new_block_button = QPushButton("New Custom Block")
        self.new_block_button.clicked.connect(self.block_pool.create_custom_block)
        right_layout.addWidget(self.new_block_button)

        content_layout.addLayout(right_layout)

        main_layout.addLayout(content_layout)  # add nested layout to main_layout


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

    def open_month_view(self):
        current_day = self.day_view.current_day
        self.open_month.emit(current_day.month, current_day.year)

    def open_week_view(self):
        current_day = self.day_view.current_day
        week_start = current_day - timedelta(days=current_day.weekday())
        self.open_week.emit(week_start)
