from cmath import rect
from PyQt5.QtWidgets import (
   QWidget, QVBoxLayout, QScrollArea, QListWidgetItem, QDialog, QListWidget, 
   QHBoxLayout, QSizePolicy, QMenu
)
from PyQt5.QtGui import QFont, QPainter, QColor, QDrag
from PyQt5.QtCore import (
    Qt, pyqtSignal, QRect, QMimeData, QByteArray, QPoint
)
from numpy import block
from blocks import task, eventblock
from datetime import datetime, timedelta, date, time
from dialogs import AddTaskDialog, AddEventDialog


class DayView(QWidget):
    def __init__(self, schedule, util, parent=None):
        super().__init__(parent)
        self.schedule = schedule
        self.util = util
        self.block_rects = []
        self.ghost_rects = []

        # ----- constants -----
        self.hour_height = 120
        self.main_line_height = 2
        self.faint_line_height = 1
        self.num_faint_lines = 3
        self.segment_spacing = (
            self.hour_height
            - self.main_line_height
            - (self.faint_line_height * self.num_faint_lines)
        ) / (self.num_faint_lines + 1)

        self.dragging_block = None
        self.drag_offset = 0
        self.resizing_block = None
        self.dragging_block = None   # for moving an existing block
        self.incoming_block = None

        self.grid_color_light = self.util.tm.get_colour(self.util.settings.theme, "calendar_grid_light")
        self.grid_color_dark = self.util.tm.get_colour(self.util.settings.theme, "calendar_grid_dark")
        self.text_color = self.util.tm.get_colour(self.util.settings.theme, "label_color")

        self.setMinimumHeight(24 * self.hour_height)
        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )
        self.items = self.schedule.day(date.today())
        self.setAcceptDrops(True)
        self.util.apply_theme()


    # ---------- helpers ----------
    def time_to_y(self, dt):
        minutes = dt.hour * 60 + dt.minute
        return int((minutes / (24 * 60)) * (24 * self.hour_height))

    def snap_y(self, y):
        """
        Snap a y-coordinate to the nearest 15-minute interval.
        """
        snap_height = self.hour_height / 4  # 15 minutes per block
        return round(y / snap_height) * snap_height

    # ---------- painting ----------
    def paintEvent(self, event):
        self.block_rects.clear()
        self.ghost_rects.clear()
        self.items = self.schedule.day(date.today())

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setFont(QFont("Arial", 12))

        # === GRID ===
        for hour in range(24):
            y_start = int(hour * self.hour_height)
            # main line
            painter.fillRect(50, y_start, self.width() - 50, self.main_line_height, self.grid_color_dark)

            current_y = y_start + self.main_line_height
            for _ in range(self.num_faint_lines):
                current_y += self.segment_spacing
                painter.fillRect(50, int(current_y), self.width() - 50, self.faint_line_height, self.grid_color_light)
                current_y += self.faint_line_height

            painter.setPen(Qt.black)
            line_center = y_start + self.main_line_height / 2
            text_y = int(line_center + painter.fontMetrics().ascent() / 2)
            painter.drawText(5, text_y, f"{hour:02d}:00")

        # --- helper to draw a block ---
        def draw_block(item, rect, alpha=255):
            # background
            color = QColor("#6F4C3C")
            color.setAlpha(alpha)
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(rect, 6, 6)

            # vertical triple-dot
            dot_x = rect.right() - 12
            dot_y = rect.top() + 4
            dot_radius = 2
            dot_spacing = 6
            painter.setBrush(Qt.white)
            for i in range(3):
                painter.drawEllipse(QPoint(dot_x, dot_y + i * dot_spacing), dot_radius, dot_radius)

            # prepare text info
            lines = [
                f"{item.name}",
                f"{item.start.strftime('%H:%M')} - {(item.start + item.duration).strftime('%H:%M')}",
                f"Duration: {int(item.duration.total_seconds() // 3600)}h {(int(item.duration.total_seconds() % 3600) // 60)}m"
            ]

            if getattr(item, "type", None) == "task":
                if getattr(item, "deadline", None):
                    lines.append(f"Deadline: {item.deadline.strftime('%d/%m/%Y %H:%M')}")
            elif getattr(item, "type", None) == "event":
                lines.append(f"Priority: {getattr(item,'priority','-')}")
                lines.append(f"Repeat: {getattr(item,'repeat_count',0)} days")
                interval = getattr(item,'interval', None)
                if interval:
                    lines.append(f"Interval: {interval} min")

            if getattr(item, "location", None):
                lines.append(f"Loc: {item.location}")
            if getattr(item, "notes", None):
                lines.append(f"Notes: {item.notes}")

            # clip lines to fit rect
            text_height = rect.height() - 8
            line_height = painter.fontMetrics().height()
            max_lines = max(1, text_height // line_height)
            lines_to_draw = lines[:max_lines]

            painter.setPen(Qt.white)
            painter.drawText(
                QRect(rect.left() + 5, rect.top() + 4, rect.width() - 20, rect.height() - 4),
                Qt.TextWordWrap,
                "\n".join(lines_to_draw)
            )

        # === BLOCKS ===
        for item in self.items:
            if item is self.dragging_block:
                continue  # ghost handled separately

            start = item.start
            end = start + item.duration
            y_start = self.time_to_y(start)
            y_end = self.time_to_y(end)
            height = max(4, y_end - y_start)
            rect = QRect(60, int(y_start + 2), int(self.width() - 80), int(height - 4))

            draw_block(item, rect)
            self.block_rects.append((rect, item))

        # === GHOST BLOCK ===
        ghost = self.dragging_block or self.incoming_block
        if ghost:
            if isinstance(ghost, dict):
                start = ghost.get("ghost_start")
                duration = ghost.get("ghost_duration", timedelta(minutes=60))
                name = ghost.get("name", "Block")
            else:
                start = getattr(ghost, "start", None)
                duration = getattr(ghost, "duration", None)
                name = getattr(ghost, "name", str(ghost))
                if hasattr(ghost, "ghost_start"):
                    start = ghost.ghost_start

            if start and duration:
                rect = QRect(60, int(self.time_to_y(start) + 2), int(self.width() - 80), int(max(4, self.time_to_y(start + duration) - self.time_to_y(start) - 4)))
                draw_block(ghost, rect, alpha=120)
                self.ghost_rects.append((rect, ghost))

    def mousePressEvent(self, event):
        click_x = event.x()
        click_y = event.y()

        # Use the rects stored in paintEvent
        for rect, item in reversed(self.block_rects):  # topmost first
            # triple-dot menu rect
            dot_size = 20
            menu_rect = QRect(rect.right() - dot_size, rect.top(), dot_size, dot_size)
            if menu_rect.contains(click_x, click_y):
                self.show_block_menu(item, event.globalPos())
                return

            # resize logic
            if abs(click_y - rect.top()) <= 6:
                self.resizing_block = (item, 'top')
                return
            elif abs(click_y - rect.bottom()) <= 6:
                self.resizing_block = (item, 'bottom')
                return

            # drag logic
            if rect.contains(click_x, click_y):
                self.dragging_block = item
                self.drag_offset = click_y - rect.top()
                return


    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-block"):
            event.acceptProposedAction()

    def mouseMoveEvent(self, event):
        if self.dragging_block:
            y = event.y() - self.drag_offset
            snapped_y = self.snap_y(y)
            total_minutes = int((snapped_y / self.hour_height) * 60)
            # Store ghost time as datetime
            start = self.dragging_block.start
            ghost_start = start.replace(hour=total_minutes // 60, minute=total_minutes % 60)
            self.dragging_block.ghost_start = ghost_start
            self.update()
        elif self.resizing_block:
            block, edge = self.resizing_block
            y = event.y()
            snapped_y = self.snap_y(y)
            total_minutes = int((snapped_y / self.hour_height) * 60)

            start = block.start
            end = start + block.duration

            if edge == 'top':
                # new start time
                new_start = datetime.combine(start.date(), time(total_minutes // 60, total_minutes % 60))
                # Ensure duration is at least 15 minutes
                new_duration = max(timedelta(minutes=15), end - new_start)
                block.start = new_start
                block.duration = new_duration
            elif edge == 'bottom':
                # new end time
                new_end = datetime.combine(start.date(), time(total_minutes // 60, total_minutes % 60))
                # Ensure duration is at least 15 minutes
                new_duration = max(timedelta(minutes=15), new_end - start)
                block.duration = new_duration

            # Update GUI immediately
            self.update()

    def mouseReleaseEvent(self, event):
        if self.dragging_block:
            if hasattr(self.dragging_block, 'ghost_start'):
                # Apply ghost_start to actual start
                self.dragging_block.start = self.dragging_block.ghost_start
                delattr(self.dragging_block, 'ghost_start')

                # Reschedule everything else
                self.schedule.global_edf_scheduler(ignore_blocks=[self.dragging_block])

        if self.resizing_block:
            # Reschedule everything except the block being resized (optional)
            block, _ = self.resizing_block
            self.schedule.global_edf_scheduler(ignore_blocks=[block])

            # Refresh GUI
            self.items = self.schedule.day(date.today())
            self.update()

        self.dragging_block = None
        self.resizing_block = None
        self.update()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-block"):
            event.acceptProposedAction()
            y = event.pos().y()
            snapped_y = self.snap_y(y)
            total_minutes = int((snapped_y / self.hour_height) * 60)
            ghost_start = datetime.combine(date.today(), datetime.min.time()) + timedelta(minutes=total_minutes)

            data = eval(event.mimeData().data("application/x-block").data().decode())

            # Add ghost start and default duration (for preview)
            y = event.pos().y()
            snapped_y = self.snap_y(y)
            total_minutes = int((snapped_y / self.hour_height) * 60)
            ghost_start = datetime.combine(date.today(), datetime.min.time()) + timedelta(minutes=total_minutes)

            data['ghost_start'] = ghost_start
            data['ghost_duration'] = timedelta(minutes=data.get('duration', 60))  # default 60 mins

            self.incoming_block = data
            self.update()


            self.incoming_block = data
            self.update()

    def dropEvent(self, event):
        if not event.mimeData().hasFormat("application/x-block"):
            return

        event.acceptProposedAction()

        # Decode dragged block type
        data = eval(event.mimeData().data("application/x-block").data().decode())
        block_type = data.get("type", "task")  # default to task

        # Compute start time from drop position
        y = event.pos().y()
        snapped_y = self.snap_y(y)
        total_minutes = int((snapped_y / self.hour_height) * 60)
        default_start = datetime.combine(date.today(), datetime.min.time()) + timedelta(minutes=total_minutes)

        if block_type.lower() == "task":
            # Open task dialog with default start
            dlg = AddTaskDialog(utils=self.util, default_start=default_start, parent=self)
            if dlg.exec_() != QDialog.Accepted:
                self.incoming_block = None
                self.update()
                return
            block_data = dlg.get_data()

            start = block_data["start"] or default_start

            # Create Task block
            block = task(
                name=block_data["name"],
                duration=block_data["duration"],
                start=start,
                deadline=block_data["deadline"],
                location=block_data["location"],
                notes=block_data["notes"]
            )

        elif block_type.lower() == "event":
            # Open event dialog with default start
            dlg = AddEventDialog(utils=self.util, default_start=default_start, parent=self)
            if dlg.exec_() != QDialog.Accepted:
                self.incoming_block = None
                self.update()
                return
            event_data = dlg.get_data()

            # Create Event block
            block = eventblock(
                name=event_data["name"],
                start=event_data["start"],  # start required in dialog
                duration=event_data["duration"],
                location=event_data["location"],
                notes=event_data["notes"],
                priority=event_data["priority"],
                repeatable=event_data["repeatable"],
                interval=event_data["interval"]
            )

        # Add block to schedule
        self.schedule.add_block(block)

        # Refresh DayView items and GUI
        self.items = self.schedule.day(date.today())
        self.incoming_block = None
        self.update()

    def dragLeaveEvent(self, event):
        self.incoming_block = None
        self.update()  

    def show_block_menu(self, block, global_pos):
        menu = QMenu(self)
        menu.addAction("Edit", lambda b=block: self.edit_block(b))
        menu.addAction("Delete", lambda b=block: self.delete_block(b))
        menu.addAction("Inspect", lambda b=block: self.inspect_block(b))
        menu.exec_(global_pos)

    def edit_block(self, block):
        if getattr(block, "type", None) == "task":
            dialog = AddTaskDialog(self.util, default_start=block.start, parent=self)
            # prefill existing data
            dialog.name_input.setText(block.name)
            dialog.duration_input.setValue(int(block.duration.total_seconds() // 60))
            if block.deadline:
                dialog.deadline_input.setDateTime(block.deadline)
            if block.start:
                dialog.start_input.setDateTime(block.start)
            if block.location:
                dialog.location_input.setText(block.location)
            if block.notes:
                dialog.notes_input.setText(block.notes)

            if dialog.exec_() == QDialog.Accepted:
                data = dialog.get_data()
                block.name = data["name"]
                block.start = data["start"]
                block.duration = data["duration"]
                block.deadline = data["deadline"]
                block.location = data.get("location")
                block.notes = data.get("notes")
                self.update()

        elif getattr(block, "type", None) == "event":
            dialog = AddEventDialog(self.util, default_start=block.start, parent=self)
            # prefill existing data
            dialog.name_input.setText(block.name)
            dialog.duration_input.setValue(int(block.duration.total_seconds() // 60))
            if block.start:
                dialog.start_input.setDateTime(block.start)
            dialog.priority_input.setCurrentIndex(getattr(block, "priority", 0))
            repeatable = getattr(block, "repeatable", False)
            dialog.repeatable_input.setCurrentIndex(1 if repeatable else 0)
            dialog.interval_input.setValue(getattr(block, "interval", 1))

            if dialog.exec_() == QDialog.Accepted:
                data = dialog.get_data()
                block.name = data["name"]
                block.start = data["start"]
                block.duration = data["duration"]
                block.priority = data["priority"]
                block.repeatable = data["repeatable"]
                block.interval = data["interval"]
                self.update()
        self.schedule.global_edf_scheduler()

    def delete_block(self, block):
        if block in self.schedule.blocks:
            self.schedule.remove_block(block)
            self.update()

    def inspect_block(self, block):
        info_lines = [
            f"Name: {block.name}",
            f"Start: {block.start}",
            f"End: {block.start + block.duration}",
            f"Duration: {int(block.duration.total_seconds()//3600)}h {(int(block.duration.total_seconds()%3600)//60)}m",
            f"Type: {getattr(block,'type','-')}",
        ]

        if getattr(block,'type',None) == "task":
            info_lines.append(f"Deadline: {getattr(block,'deadline','-')}")
        elif getattr(block,'type',None) == "event":
            info_lines.append(f"Priority: {getattr(block,'priority','-')}")
            info_lines.append(f"Repeatable: {'Yes' if getattr(block,'repeatable',False) else 'No'}")
            interval = getattr(block,'interval',None)
            if interval:
                info_lines.append(f"Interval: {interval} days")

        if getattr(block,'location',None):
            info_lines.append(f"Location: {block.location}")
        if getattr(block,'notes',None):
            info_lines.append(f"Notes: {block.notes}")

        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "Inspect Block", "\n".join(info_lines))

class BlockPool(QListWidget):   
    def __init__(self, day_view):
        super().__init__()
        self.day_view = day_view
        self.setFixedWidth(200)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDefaultDropAction(Qt.CopyAction)

        # Only two draggable items: Task and Event
        blocks = [
            {"name": "Task", "type": "task"},
            {"name": "Event", "type": "event"}
        ]

        for b in blocks:
            item = QListWidgetItem(b["name"])
            item.setData(Qt.UserRole, b)
            self.addItem(item)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if not item:
            return

        data = item.data(Qt.UserRole)

        mime = QMimeData()
        mime.setData(
            "application/x-block",
            QByteArray(str(data).encode())
        )

        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(Qt.CopyAction)

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

        # Right: BlockPool
        self.block_pool = BlockPool(self.day_view)
        layout.addWidget(self.block_pool, 1)
        main_layout.addLayout(layout)
