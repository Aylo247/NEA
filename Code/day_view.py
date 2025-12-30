from PyQt5.QtWidgets import QWidget, QScrollArea, QSizePolicy
from PyQt5.QtGui import QFont, QPainter, QColor, QPen
from PyQt5.QtCore import Qt, QRect, QPoint, QTimer
from datetime import datetime, timedelta, date, time
from day_view_mouse_mixin import DayViewMouseMixin
from day_view_menu_mixin import DayViewMenuMixin


class DayView(QWidget, DayViewMouseMixin, DayViewMenuMixin):
    def __init__(self, schedule, util, custom_blocks, parent=None):
        super().__init__(parent)
        self.schedule = schedule
        self.util = util
        self.theme = self.util.settings.theme
        self.update_theme_colours()
        self.block_rects = []
        self.ghost_rects = []
        self.custom_blocks = custom_blocks

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

        self.setMinimumHeight(24 * self.hour_height)
        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )
        self.set_current_day(date.today())

        self.setAcceptDrops(True)
        self.util.apply_theme()
        QTimer.singleShot(0, self.scroll_to_current_time)
        self.current_minute = datetime.now().minute
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_minute_change)
        self.timer.start(1000)  # check every second

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

    def set_current_day(self, date):
        self.current_day = date
        self.load_blocks_for_day()   # update items for the day
        self.update()
        QTimer.singleShot(0, self.scroll_to_current_time)

    def load_blocks_for_day(self):
        # Filter blocks from the schedule for this day
        self.block_rects.clear()
        self.items = self.schedule.day(self.current_day)

    def draw_block(self, item, rect, painter,alpha=200):
        # vertical triple-dot
        dot_x = rect.right() - 12
        dot_y = rect.top() + 8
        dot_radius = 2
        dot_spacing = 6

        # prepare text info
        if isinstance(item, dict):
            color = self.col_block_default

            # Determine dot colour based on block colour brightness
            h, s, v, _ = color.getHsvF()  # get HSV values

            # adjust brightness
            if v > 0.5:
                # block is light → make dots darker
                v = max(0, v - 0.4)
            else:
                # block is dark → make dots lighter
                v = min(1, v + 0.4)

            dot_color = QColor()
            dot_color.setHsvF(h, s, v, 1.0)
            painter.setBrush(dot_color)
            for i in range(3):
                painter.drawEllipse(QPoint(dot_x, dot_y + i * dot_spacing), dot_radius, dot_radius)

            color.setAlpha(alpha)
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(rect, 6, 6)
            name = item.get("name", "Block")
            start = item.get("ghost_start") or datetime.combine(date.today(), time(0,0))
            duration = item.get("ghost_duration", timedelta(minutes=60))
            lines = [
                f"{name}",
                f"{start.strftime('%H:%M')} - {(start + duration).strftime('%H:%M')}",
                f"Duration: {int(duration.total_seconds() // 3600)}h {(int(duration.total_seconds() % 3600) // 60)}m"
            ]
        else:
            color = QColor(item.colour) if getattr(item, "colour", None) else self.col_block_default

            # Determine dot colour based on block colour brightness
            h, s, v, a = color.getHsvF()  # get HSV values

            # adjust brightness
            if v > 0.5:
                # block is light → make dots darker
                v = max(0, v - 0.4)
            else:
                # block is dark → make dots lighter
                v = min(1, v + 0.4)

            dot_color = QColor()
            dot_color.setHsvF(h, s, v, 1.0)
            painter.setBrush(dot_color)
            for i in range(3):
                painter.drawEllipse(QPoint(dot_x, dot_y + i * dot_spacing), dot_radius, dot_radius)

            color.setAlpha(alpha)
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(rect, 6, 6)
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

    def update_theme_colours(self):
        tm = self.util.tm
        theme = self.util.settings.theme
        self.col_block_default = tm.get_colour(theme, "default_block")
        self.col_pointer = tm.get_colour(theme, "current_time_pointer")
        self.col_grid_light = tm.get_colour(theme, "calendar_grid_light")
        self.col_grid_dark = tm.get_colour(theme, "calendar_grid_dark")
        self.col_text = tm.get_colour(theme, "label_color")

    # ---------- painting ----------
    def paintEvent(self, event):
        self.block_rects.clear()
        self.ghost_rects.clear()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setFont(QFont("Arial", 12))

        # === GRID ===
        for hour in range(24):
            y_start = int(hour * self.hour_height)
            # main line
            painter.fillRect(50, y_start, self.width() - 50, self.main_line_height, self.col_grid_dark )

            current_y = y_start + self.main_line_height
            for _ in range(self.num_faint_lines):
                current_y += self.segment_spacing
                painter.fillRect(50, int(current_y), self.width() - 50, self.faint_line_height, self.col_grid_light)
                current_y += self.faint_line_height

            painter.setPen(Qt.black)
            line_center = y_start + self.main_line_height / 2
            text_y = int(line_center + painter.fontMetrics().ascent() / 2)
            painter.drawText(5, text_y, f"{hour:02d}:00")

        # === CURRENT TIME LINE WITH STADIUM LABEL ===
        now = datetime.now() 
        if now.date() == self.current_day:
            y_now = self.time_to_y(now)
            line_color = self.col_pointer
            line_color.setAlpha(200) 

            # Draw the horizontal line
            painter.setPen(QPen(line_color, 2))
            painter.drawLine(50, y_now, self.width(), y_now)

            # Draw the stadium/obround for the time label
            time_text = now.strftime("%H:%M")
            font_metrics = painter.fontMetrics()
            text_width = font_metrics.width(time_text) + 10  # padding
            text_height = font_metrics.height()

            stadium_rect = QRect(
                5,                        # x-position (left margin)
                int(y_now - text_height / 2),  # center vertically on line
                text_width,
                text_height
            )

            painter.setPen(Qt.NoPen)
            painter.setBrush(line_color)
            painter.drawRoundedRect(stadium_rect, text_height / 2, text_height / 2)  # radius = half height for stadium

            # Draw the time text inside the stadium
            painter.setPen(Qt.white)
            painter.drawText(stadium_rect, Qt.AlignCenter, time_text)

        # === BLOCKS ===
        for item in self.items:
            if item is self.dragging_block:
                continue  # ghost handled separately
            
            if hasattr(item, "is_completed"):
                if item.is_completed:
                    continue

            start = item.start
            end = start + item.duration
            y_start = self.time_to_y(start)
            y_end = self.time_to_y(end)
            height = max(4, y_end - y_start)
            rect = QRect(60, int(y_start + 2), int(self.width() - 80), int(height - 4))

            self.draw_block(item, rect, painter)
            self.block_rects.append((rect, item))

        # === GHOST BLOCK ===
        ghost = self.dragging_block or self.incoming_block
        if ghost:
            if isinstance(ghost, dict):  # incoming block
                start = ghost.get("ghost_start")
                duration = ghost.get("ghost_duration", timedelta(minutes=60))
            else:  # existing block
                start = getattr(ghost, "ghost_start", None)
                duration = getattr(ghost, "duration", None)

            if start and duration:
                rect = QRect(
                    60,
                    int(self.time_to_y(start) + 2),
                    int(self.width() - 80),
                    int(max(4, self.time_to_y(start + duration) - self.time_to_y(start) - 4))
                )
                self.draw_block(ghost, rect, painter, alpha=120)
                self.ghost_rects.append((rect, ghost))

    def find_nearest_non_colliding(self, start_time, duration):
        """
        Returns the nearest start_time that does not overlap any fixed block
        and stays within the day boundaries.
        """
        fixed_blocks = sorted(
            [b for _, b in self.block_rects if getattr(b, "is_fixed", False)],
            key=lambda b: b.start
        )

        candidate_start = start_time
        candidate_end = candidate_start + duration
        day_start = datetime.combine(candidate_start.date(), time(0, 0))
        day_end = datetime.combine(candidate_start.date(), time(23, 59))

        # Avoid overlapping fixed blocks
        for fb in fixed_blocks:
            fb_start = fb.start
            fb_end = fb.start + fb.duration

            if candidate_start < fb_end and candidate_end > fb_start:
                # push candidate_start just after the fixed block
                candidate_start = fb_end
                candidate_end = candidate_start + duration

        # Clamp within day boundaries
        if candidate_start < day_start:
            candidate_start = day_start
        if candidate_end > day_end:
            candidate_start = day_end - duration

        return candidate_start

    def scroll_to_current_time(self):
        # find scroll area parent
        scroll_area = self.parent()
        while scroll_area and not isinstance(scroll_area, QScrollArea):
            scroll_area = scroll_area.parent()
        if not scroll_area:
            return

        hour_buffer = timedelta(hours=1)  # buffer for scrolling
        today = date.today()

        if self.current_day == today:
            # Scroll to current time minus buffer
            now = datetime.now()
            scroll_time = now - hour_buffer
            if scroll_time.time() < time(0, 0):
                scroll_time = datetime.combine(today, time(0, 0))
            y = self.time_to_y(scroll_time)
            scroll_area.verticalScrollBar().setValue(max(0, y))

        elif self.items:
            # Scroll to first block minus buffer
            first_block = min(self.items, key=lambda b: b.start)
            scroll_time = first_block.start - hour_buffer
            if scroll_time.time() < time(0, 0):
                scroll_time = datetime.combine(first_block.start.date(), time(0, 0))
            y = self.time_to_y(scroll_time)
            scroll_area.verticalScrollBar().setValue(max(0, y))

        else:
            # No blocks, scroll to start of day plus buffer
            scroll_time = datetime.combine(self.current_day, time(0, 0)) + hour_buffer
            y = self.time_to_y(scroll_time)
            scroll_area.verticalScrollBar().setValue(max(0, y))

    def check_minute_change(self):
        now = datetime.now()
        if now.minute != self.current_minute:
            self.current_minute = now.minute
            self.update_current_time()

    def update_current_time(self):
        self.current_time = datetime.now()
        self.update()  # triggers paintEvent