from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import QRect
from datetime import datetime, timedelta, date, time
from dialogs import AddTaskDialog, AddEventDialog
from blocks import Task, EventBlock
import pickle


class DayViewMouseMixin:
    """handles mouse interactions and drag-and-drop behavior for DayView blocks"""

    # drag and drop events
    def dragEnterEvent(self, event) -> None:
        """handle drag entering the DayView; initialise ghost block if valid"""
        if not event.mimeData().hasFormat("application/x-block"):
            return

        try:
            data = pickle.loads(event.mimeData().data("application/x-block"))
        except Exception:
            return

        if data.get("type") not in ["task", "event"] and not self.custom_blocks:
            return

        event.acceptProposedAction()
        self.incoming_block = data.copy()
        self.incoming_block['ghost_start'] = datetime.combine(date.today(), datetime.min.time())
        duration = data.get("duration", 60)
        if not isinstance(duration, timedelta):
            duration = timedelta(minutes=duration)
        self.incoming_block['ghost_duration'] = duration
        self.update()

    def dragMoveEvent(self, event) -> None:
        """update ghost start times while dragging existing or incoming blocks"""
        if not event.mimeData().hasFormat("application/x-block"):
            return

        event.acceptProposedAction()
        y = event.pos().y()
        snapped_y = self.snap_y(y)
        total_minutes = int((snapped_y / self.hour_height) * 60)

        if self.incoming_block:
            duration = timedelta(minutes=self.incoming_block.get("duration", 60))
            ghost_start = datetime.combine(date.today(), datetime.min.time()) + timedelta(minutes=total_minutes)

            now = datetime.now()

            if ghost_start < now:
                ghost_start = now

            ghost_start = self.find_nearest_non_colliding(ghost_start, duration)
            self.incoming_block['ghost_start'] = ghost_start
            self.incoming_block['ghost_duration'] = duration
            if 'name' not in self.incoming_block:
                self.incoming_block['name'] = "New Block"
            self.update()

    def dropEvent(self, event) -> None:
        """handle dropping of blocks from pool or other DayViews"""
        if not event.mimeData().hasFormat("application/x-block"):
            return

        event.acceptProposedAction()
        data = pickle.loads(event.mimeData().data("application/x-block"))
        y = event.pos().y()
        snapped_y = self.snap_y(y)
        total_minutes = int((snapped_y / self.hour_height) * 60)
        default_start = datetime.combine(date.today(), datetime.min.time()) + timedelta(minutes=total_minutes)
        block = None

        # Handle custom block templates
        if data.get("is_custom", False):
            block_type = data.get("type", "task")
            template = next((t for t in self.custom_blocks.templates if t["name"] == data["name"]), {})
            fixed_attrs = {k: v for k, v in template.items() if k not in ["type"]}

            if block_type == "task":
                dlg = AddTaskDialog(utils=self.util, default_start=default_start, fixed_attrs=fixed_attrs, parent=self)
            elif block_type == "event":
                dlg = AddEventDialog(utils=self.util, default_start=default_start, fixed_attrs=fixed_attrs, parent=self)
            else:
                return

            if dlg.exec_() != QDialog.Accepted:
                self.incoming_block = None
                self.update()
                return

            user_data = dlg.get_data()
            merged_data = {**fixed_attrs, **user_data}
            block = self.custom_blocks.instantiate(data["name"], **merged_data)

        # Handle default blocks
        else:
            block_type = data.get("type", "task").lower()
            if block_type == "task":
                dlg = AddTaskDialog(utils=self.util, default_start=default_start, parent=self)
                if dlg.exec_() != QDialog.Accepted:
                    self.incoming_block = None
                    self.update()
                    return
                block_data = dlg.get_data()
                start = block_data.get("start") or default_start
                block = Task(
                    name=block_data["name"],
                    duration=block_data["duration"],
                    start=start,
                    deadline=block_data["deadline"],
                    location=block_data["location"],
                    notes=block_data["notes"],
                    colour=block_data["colour"]
                )

            elif block_type == "event":
                dlg = AddEventDialog(utils=self.util, default_start=default_start, parent=self)
                if dlg.exec_() != QDialog.Accepted:
                    self.incoming_block = None
                    self.update()
                    return
                event_data = dlg.get_data()
                block = EventBlock(
                    name=event_data["name"],
                    start=event_data["start"],
                    duration=event_data["duration"],
                    location=event_data["location"],
                    notes=event_data["notes"],
                    priority=event_data["priority"],
                    repeatable=event_data["repeatable"],
                    interval=event_data["interval"],
                    colour=event_data.get("colour", "#453434")
                )

        if block:
            self.schedule.add_block(block)
            self.items = self.schedule.day(date.today())
            self.incoming_block = None
            self.update()

    def dragLeaveEvent(self, event) -> None:
        """remove ghost preview when the drag leaves the DayView"""
        self.incoming_block = None
        self.update()

    # mouse events
    def mousePressEvent(self, event) -> None:
        """detect clicks on blocks for dragging, resizing, or opening the block menu"""
        click_x, click_y = event.x(), event.y()

        for rect, item in reversed(self.block_rects):  # topmost first
            dot_size = 20
            menu_rect = QRect(rect.right() - dot_size, rect.top(), dot_size, dot_size)
            if menu_rect.contains(click_x, click_y):
                self.show_block_menu(item, event.globalPos())
                return

            if getattr(item, "is_fixed", True):
                continue

            # Resizing
            if abs(click_y - rect.top()) <= 6:
                self.resizing_block = (item, 'top')
                return
            elif abs(click_y - rect.bottom()) <= 6:
                self.resizing_block = (item, 'bottom')
                return

            # Dragging
            if rect.contains(click_x, click_y):
                self.dragging_block = item
                self.drag_offset = click_y - rect.top()
                return

    def mouseMoveEvent(self, event) -> None:
        """update positions of dragged or resizing blocks, and ghost previews"""
        if self.dragging_block and not getattr(self.dragging_block, "is_fixed", False):
            y = event.y() - self.drag_offset
            snapped_y = self.snap_y(y)
            total_minutes = int((snapped_y / self.hour_height) * 60)

            start = self.dragging_block.start
            ghost_start = start.replace(hour=total_minutes // 60, minute=total_minutes % 60)

            now = datetime.now()
            block_active = start <= now <= start + self.dragging_block.duration

            if block_active:
                # cannot drag before original start
                if ghost_start < start:
                    ghost_start = start
            else:
                # cannot drag before current time
                if ghost_start < now:
                    ghost_start = now

            ghost_start = self.find_nearest_non_colliding(ghost_start, self.dragging_block.duration)
            self.dragging_block.ghost_start = ghost_start
            self.update()

        elif self.resizing_block:
            block, edge = self.resizing_block
            y = event.y()
            snapped_y = self.snap_y(y)
            total_minutes = int((snapped_y / self.hour_height) * 60)
            start = block.start
            end = start + block.duration
            new_time = datetime.combine(start.date(), time(total_minutes // 60, total_minutes % 60))

            now = datetime.now()
            block_active = start <= now <= end  # currently active block

            if edge == 'top':
                new_start = new_time

                if block_active and new_start < start:
                    new_start = start
                elif not block_active and new_start < now:
                    new_start = now

                # collision with fixed blocks
                for _, fb in self.block_rects:
                    if getattr(fb, "is_fixed", False):
                        fb_start = fb.start
                        fb_end = fb.start + fb.duration
                        if new_start < fb_end and end > fb_start:
                            new_start = fb_end

                block.start = new_start
                block.duration = max(timedelta(minutes=15), end - new_start)

            elif edge == 'bottom':
                new_end = new_time

                # collision with fixed blocks
                for _, fb in self.block_rects:
                    if getattr(fb, "is_fixed", False):
                        fb_start = fb.start
                        fb_end = fb.start + fb.duration
                        if start < fb_end and new_end > fb_start:
                            new_end = fb_start

                block.duration = max(timedelta(minutes=15), new_end - start)

            self.update()

    def mouseReleaseEvent(self, event) -> None:
        """finalize drag or resize operations and update schedule"""
        if self.dragging_block and hasattr(self.dragging_block, 'ghost_start'):
            self.dragging_block.start = self.dragging_block.ghost_start
            delattr(self.dragging_block, 'ghost_start')
            self.schedule.global_edf_scheduler(ignore_blocks=[self.dragging_block])

        if self.resizing_block:
            block, _ = self.resizing_block
            self.schedule.global_edf_scheduler(ignore_blocks=[block])
            self.items = self.schedule.day(date.today())
            self.update()

        self.dragging_block = None
        self.resizing_block = None
        self.update()

    def can_drag_block(self, block, new_start_time):
        """
        determines if a block can be dragged to `new_start_time`.
        
        rules:
        1. cannot go before current time.
        2. if currently active block, can move forward, but not before its original start.
        """
        now = datetime.now()
        
        # is block currently active?
        block_active = block.start <= now <= block.end

        if block_active:
            # can move forward, but not before original start
            if new_start_time < block.start:
                return False
        else:
            # cannot move before current time
            if new_start_time < now:
                return False

        return True
