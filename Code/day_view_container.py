from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QHBoxLayout,
    QPushButton, QLabel, QDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from datetime import timedelta
from day_view import DayView
from block_pool import BlockPool
from dialogs import ClearDayDialog
import pickle


class DayViewScroll(QScrollArea):
    """
    scrollable wrapper around DayView to handle drag-and-drop

    handles incoming blocks from the BlockPool or other DayViews
    """

    def __init__(self, day_view) -> None:
        super().__init__()
        self.setWidgetResizable(True)
        self.setWidget(day_view)
        self.viewport().setAcceptDrops(True)
        self.day_view = day_view

    def dragEnterEvent(self, event) -> None:
        """handle block entering the scroll area"""
        if event.mimeData().hasFormat("application/x-block"):
            event.acceptProposedAction()
            data_bytes = event.mimeData().data("application/x-block")
            data = pickle.loads(data_bytes)
            
            self.day_view.incoming_block = data.copy()
            self.day_view.update()
            
    def dragMoveEvent(self, event) -> None:
        """dorward drag move event to the DayView"""
        self.day_view.dragMoveEvent(event)

    def dropEvent(self, event) -> None:
        """forward drop event to the DayView and clear incoming block"""
        if not event.mimeData().hasFormat("application/x-block"):
            return

        mapped_pos = self.day_view.mapFrom(self.viewport(), event.pos())
        event._mapped_pos = mapped_pos
        event.setDropAction(Qt.CopyAction)
        event.accept()

        self.day_view.dropEvent(event)
        self.day_view.incoming_block = None


class DayViewContainer(QWidget):
    """
    container widget combining DayView, BlockPool, and header controls

    includes:
    - top header bar with navigation and settings buttons
    - day label with previous/next buttons
    - main content area with scrollable DayView
    - blockPool sidebar with custom block creation
    """

    # signals to communicate with parent or other modules
    open_settings = pyqtSignal()
    open_todo = pyqtSignal()
    back = pyqtSignal()
    open_month = pyqtSignal(object, object)
    open_week = pyqtSignal(object)

    def __init__(self, schedule, utils, customs) -> None:
        super().__init__()

        self.setWindowTitle("day view")

        self.schedule = schedule
        self.utils = utils

        # main vertical layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # header
        header_bar, buttons = utils.create_top_bar(
            show_back=True, show_settings=True, show_todo=True,
            show_month=True, show_week=True
        )
        main_layout.addWidget(header_bar)

        # connect header buttons
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

        

        # day navigation header
        day_header_layout = QHBoxLayout()

        self.clear_day_btn = QPushButton("Clear Day")

        self.prev_day_btn = QPushButton("<")
        self.next_day_btn = QPushButton(">")
        self.day_label = QLabel()
        self.day_label.setAlignment(Qt.AlignCenter)

        day_header_layout.addWidget(self.clear_day_btn)
        day_header_layout.addWidget(self.prev_day_btn)
        day_header_layout.addWidget(self.day_label)
        day_header_layout.addWidget(self.next_day_btn)
        main_layout.addLayout(day_header_layout)

        # connect day navigation buttons
        self.clear_day_btn.clicked.connect(self.clear_day)
        
        self.prev_day_btn.clicked.connect(self.go_to_prev_day)
        self.next_day_btn.clicked.connect(self.go_to_next_day)

        # content
        content_layout = QHBoxLayout()

        # Left: Scrollable DayView
        self.day_view = DayView(self.schedule, self.utils, customs)
        scroll = DayViewScroll(self.day_view)
        scroll.setAcceptDrops(True)
        scroll.viewport().setAcceptDrops(True)
        content_layout.addWidget(scroll, 3)

        # right: BlockPool and "new custom block" button
        right_layout = QVBoxLayout()
        self.block_pool = BlockPool(self.day_view, customs)
        right_layout.addWidget(self.block_pool)

        self.new_block_button = QPushButton("new custom block")
        self.new_block_button.clicked.connect(self.block_pool.create_custom_block)
        right_layout.addWidget(self.new_block_button)

        content_layout.addLayout(right_layout)
        main_layout.addLayout(content_layout)

        self.utils.apply_theme()

    # day navigation methods 
    def set_current_day(self, day_date) -> None:
        """set the currently displayed day and update the label"""
        self.day_view.set_current_day(day_date)
        self.update_day_label()

    def update_day_label(self) -> None:
        """update the day label to show the current day"""
        self.day_label.setText(self.day_view.current_day.strftime("%A, %d %B %Y"))

    def go_to_prev_day(self) -> None:
        """move to the previous day"""
        if self.day_view.current_day:
            self.day_view.set_current_day(self.day_view.current_day - timedelta(days=1))
            self.update_day_label()

    def go_to_next_day(self) -> None:
        """move to the next day"""
        if self.day_view.current_day:
            self.day_view.set_current_day(self.day_view.current_day + timedelta(days=1))
            self.update_day_label()

    def open_month_view(self) -> None:
        """emit signal to open the month view"""
        current_day = self.day_view.current_day
        self.open_month.emit(current_day.month, current_day.year)

    def open_week_view(self) -> None:
        """emit signal to open the week view"""
        current_day = self.day_view.current_day
        week_start = current_day - timedelta(days=current_day.weekday())
        self.open_week.emit(week_start)

    def clear_day(self) -> None:
        dlg = ClearDayDialog(parent=self)

        if dlg.exec_() != QDialog.Accepted:
            return  # user cancelled

        mode, hours = dlg.get_result()

        if mode == "rest_of_day":
            self.schedule.clear_for_time("rest of day")
        else:
            self.schedule.clear_for_time(hours)
