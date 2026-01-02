from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QScrollArea,
    QLabel, QSizePolicy, QPushButton
)
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QMimeData
from PyQt5.QtGui import QDrag, QPainter
from datetime import datetime, timedelta, time
from day_view import DayView
from functools import partial
import pickle

class ClickableLabel(QLabel):
    """
    a QLabel that emits a clicked signal and acts like a button
    """
    clicked = pyqtSignal()

    def mousePressEvent(self, event) -> None:
        # emit clicked signal when label is pressed
        self.clicked.emit()
        super().mousePressEvent(event)


class WeekDayView(DayView):
    """
    subclass of DayView for use in a week view container
    handles painting, ghost blocks, and mouse interactions
    """
    def __init__(self, schedule, util, parent: QWidget | None = None):
        # initialize WeekDayView with schedule and utility reference
        super().__init__(schedule, util, parent)
        self.show_timeline: bool = False
        self.show_current_time: bool = False
        self.week_view: "WeekViewContainer" | None = None

    # painting / drawing
    def paintEvent(self, event) -> None:
        # paint grid lines, blocks, and ghost block if dragging
        self.block_rects.clear()
        self.ghost_rects.clear()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setFont(self.font())

        # draw hour grid lines
        for hour in range(24):
            y_start = int(hour * self.hour_height)
            painter.fillRect(0, y_start, self.width(), self.main_line_height, self.col_grid_dark)
            current_y = y_start + self.main_line_height
            for _ in range(self.num_faint_lines):
                current_y += self.segment_spacing
                painter.fillRect(0, int(current_y), self.width(), self.faint_line_height, self.col_grid_light)
                current_y += self.faint_line_height

        # draw blocks
        for item in self.items:
            if getattr(item, "is_completed", False):
                continue
            if self.week_view and self.week_view.current_dragging_block is item:
                continue

            y_start = self.time_to_y(item.start)
            y_end = self.time_to_y(item.start + item.duration)
            height = max(4, y_end - y_start)
            rect = QRect(2, int(y_start + 2), int(self.width() - 4), int(height - 4))
            self.draw_block(item, rect, painter)
            self.block_rects.append((rect, item))

        # draw ghost block if dragging
        if self.week_view:
            ghost = self.week_view.current_dragging_block
            ghost_start = self.week_view.ghost_start
            if ghost and ghost_start and ghost_start.date() == self.current_day:
                rect = QRect(
                    2,
                    int(self.time_to_y(ghost_start) + 2),
                    int(self.width() - 4),
                    int(max(4, self.time_to_y(ghost_start + ghost.duration) - self.time_to_y(ghost_start) - 4))
                )
                self.draw_block(ghost, rect, painter, alpha=120)
                self.ghost_rects.append((rect, ghost))

    # mouse / drag events
    def mousePressEvent(self, event) -> None:
        # start drag if clicked on a block
        click_x, click_y = event.x(), event.y()
        if not self.week_view:
            return
        for rect, item in reversed(self.block_rects):
            if rect.contains(click_x, click_y):
                if getattr(item, "is_fixed", False) or getattr(item, "type", "task") != "task":
                    continue
                self.week_view.start_drag(item, self.current_day)
                drag = QDrag(self)
                mime = QMimeData()
                data = {"block_ref": id(item)}
                mime.setData("application/x-block", pickle.dumps(data))
                drag.setMimeData(mime)
                drag.exec_(Qt.MoveAction)
                break

    def dragEnterEvent(self, event) -> None:
        # accept drag if it has block data
        if event.mimeData().hasFormat("application/x-block"):
            event.acceptProposedAction()

    def dragMoveEvent(self, event) -> None:
        # update ghost block position while dragging
        if not self.week_view:
            return
        y = event.pos().y()
        snapped_y = self.snap_y(y)
        total_minutes = int((snapped_y / self.hour_height) * 60)
        new_time = datetime.combine(self.current_day, time(total_minutes // 60, total_minutes % 60))
        self.week_view.update_ghost(self.current_day, new_time)

    def dropEvent(self, event) -> None:
        # commit block drop on this day
        if self.week_view:
            self.week_view.commit_drop(self.current_day)

    def dragLeaveEvent(self, event) -> None:
        # clear ghost when leaving day view
        if self.week_view:
            self.week_view.update_ghost(None, None)
            self.update()


class WeekViewContainer(QWidget):
    """
    widget displaying a full week with tasks and events
    manages navigation, headers, scroll area, and drag-drop coordination
    """
    open_settings = pyqtSignal()
    open_todo = pyqtSignal()
    open_day = pyqtSignal(datetime)
    back = pyqtSignal()
    open_month = pyqtSignal(int, int)

    # initialization
    def __init__(self, schedule, util, parent: QWidget | None = None):
        # initialize week view container with schedule and util
        super().__init__(parent)
        self.schedule = schedule
        self.util = util

        self.current_dragging_block = None
        self.ghost_start: datetime | None = None
        self.drag_source_day: datetime | None = None

        self.current_week_start: datetime.date = datetime.now().date()
        if self.current_week_start.weekday() != 0:
            self.current_week_start -= timedelta(days=self.current_week_start.weekday())

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # top bar
        header_bar, buttons = self.util.create_top_bar(
            show_back=True, show_settings=True, show_todo=True,
            show_month=True, show_week=True
        )
        self.main_layout.addWidget(header_bar)
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

        # week navigation
        week_header_layout = QHBoxLayout()
        self.prev_week_btn = QPushButton("<")
        self.next_week_btn = QPushButton(">")
        self.week_label = QLabel()
        self.week_label.setAlignment(Qt.AlignCenter)
        week_header_layout.addWidget(self.prev_week_btn)
        week_header_layout.addWidget(self.week_label)
        week_header_layout.addWidget(self.next_week_btn)
        self.main_layout.addLayout(week_header_layout)
        self.update_week_label()
        self.prev_week_btn.clicked.connect(self.go_to_prev_week)
        self.next_week_btn.clicked.connect(self.go_to_next_week)

        # header row for days
        self.header_layout = QHBoxLayout()
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        self.header_layout.setSpacing(0)
        timeline_label = QLabel("")
        timeline_label.setFixedWidth(50)
        self.header_layout.addWidget(timeline_label)

        self.day_labels: list[ClickableLabel] = []
        for i in range(7):
            day = self.current_week_start + timedelta(days=i)
            day_label = ClickableLabel(day.strftime("%A\n%d %b"))
            day_label.setAlignment(Qt.AlignCenter)
            day_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            day_label.clicked.connect(partial(self.open_day.emit, day))
            self.header_layout.addWidget(day_label)
            self.day_labels.append(day_label)
        self.main_layout.addLayout(self.header_layout)

        # scroll area for day columns
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QHBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(0)
        self.scroll_area.setWidget(self.scroll_content)
        self.main_layout.addWidget(self.scroll_area)

        # timeline column
        self.timeline_layout = QVBoxLayout()
        self.timeline_layout.setContentsMargins(0, 0, 0, 0)
        self.timeline_layout.setSpacing(0)
        for h in range(24):
            label = QLabel(f"{h:02d}:00")
            label.setAlignment(Qt.AlignTop | Qt.AlignRight)
            label.setFixedHeight(60)
            self.timeline_layout.addWidget(label)

        self.day_views: list[WeekDayView] = []
        self.refresh_week_view()

    # refresh / populate week view
    def refresh_week_view(self) -> None:
        # clear previous day views
        for i in reversed(range(self.scroll_layout.count())):
            w = self.scroll_layout.itemAt(i).widget()
            if w:
                w.setParent(None)
        self.day_views.clear()

        # add timeline widget
        timeline_widget = QWidget()
        timeline_widget.setLayout(self.timeline_layout)
        self.scroll_layout.addWidget(timeline_widget)

        # add day columns
        for i in range(7):
            day_date = self.current_week_start + timedelta(days=i)
            day_view = WeekDayView(self.schedule, self.util)
            day_view.week_view = self
            day_view.set_current_day(day_date)
            day_view.show_timeline = False
            self.scroll_layout.addWidget(day_view)
            self.day_views.append(day_view)

    # week navigation
    def set_current_week(self, week_start_date: datetime.date) -> None:
        # set current week and update header labels
        self.current_week_start = week_start_date
        for i, day_label in enumerate(self.day_labels):
            day = self.current_week_start + timedelta(days=i)
            day_label.setText(day.strftime("%A\n%d %b"))
            day_label.clicked.disconnect()
            day_label.clicked.connect(partial(self.open_day.emit, day))
        self.refresh_week_view()

    def open_month_view(self) -> None:
        # emit current month and year for month view
        self.open_month.emit(self.current_week_start.month, self.current_week_start.year)

    def open_week_view(self) -> None:
        # refresh week view for current week
        self.set_current_week(self.current_week_start)

    def update_week_label(self) -> None:
        # update week label text
        self.week_label.setText(f"Week com: {self.current_week_start.strftime('%d %b %Y')}")

    def go_to_prev_week(self) -> None:
        # go to previous week
        self.current_week_start -= timedelta(days=7)
        self.update_week_label()
        self.refresh_week_view()

    def go_to_next_week(self) -> None:
        # go to next week
        self.current_week_start += timedelta(days=7)
        self.update_week_label()
        self.refresh_week_view()

    # drag / ghost block
    def start_drag(self, block, source_day: datetime) -> None:
        # initialize dragging for block
        self.current_dragging_block = block
        self.ghost_start = block.start
        self.drag_source_day = source_day
        for dv in self.day_views:
            dv.update()

    def update_ghost(self, new_day: datetime | None, new_time: datetime | None) -> None:
        # update ghost block during drag
        if self.current_dragging_block:
            self.ghost_start = new_time
            for dv in self.day_views:
                dv.update()

    def commit_drop(self, target_day: datetime) -> None:
        # commit block to new day/time
        if self.current_dragging_block:
            self.current_dragging_block.start = self.ghost_start
            self.current_dragging_block = None
            self.ghost_start = None
            self.drag_source_day = None
            for dv in self.day_views:
                dv.items = self.schedule.day(dv.current_day)
                dv.update()
