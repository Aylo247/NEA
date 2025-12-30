from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import QRect
from datetime import datetime, timedelta, date, time
from dialogs import AddTaskDialog, AddEventDialog
from blocks import task, eventblock
import pickle

class DayViewMouseMixin():
    def mousePressEvent(self, event):
        click_x, click_y = event.x(), event.y()

        for rect, item in reversed(self.block_rects):  # topmost first
            # triple-dot menu
            dot_size = 20
            menu_rect = QRect(rect.right() - dot_size, rect.top(), dot_size, dot_size)
            if menu_rect.contains(click_x, click_y):
                self.show_block_menu(item, event.globalPos())
                return

            # only tasks are draggable/resizable
            if getattr(item, "is_fixed", True):
                continue

            # resizing logic
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
            try:
                data = pickle.loads(event.mimeData().data("application/x-block"))
            except Exception:
                return  # invalid data

            if data.get("type") not in ["task", "event"] and not self.custom_blocks:
                return

            event.acceptProposedAction()
            self.incoming_block = data.copy()
            # initialise ghost start/duration for preview
            self.incoming_block['ghost_start'] = datetime.combine(date.today(), datetime.min.time())
            duration = self.incoming_block.get('duration', 60)
            if not isinstance(duration, timedelta):
                duration = timedelta(minutes=duration)
            self.incoming_block['ghost_duration'] = duration
            self.update()

    def dragLeaveEvent(self, event):
        # When leaving a DayView, remove the ghost preview
        if self.incoming_block:
            delattr(self.incoming_block, "ghost_start")
            self.incoming_block = None
            self.update()

    def mouseMoveEvent(self, event):
        if self.dragging_block and not getattr(self.dragging_block, "is_fixed", False):
            y = event.y() - self.drag_offset
            snapped_y = self.snap_y(y)
            total_minutes = int((snapped_y / self.hour_height) * 60)

            start = self.dragging_block.start
            ghost_start = start.replace(hour=total_minutes // 60, minute=total_minutes % 60)

            # --- collision avoidance ---
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

            if edge == 'top':
                # new start, stop at any fixed block below
                new_start = new_time
                for _, fb in self.block_rects:
                    if getattr(fb, "is_fixed", False):
                        fb_start = fb.start
                        fb_end = fb.start + fb.duration
                        # If new_start would overlap fb
                        if new_start < fb_end and end > fb_start:
                            new_start = fb_end  # push down to avoid collision
                block.start = new_start
                block.duration = max(timedelta(minutes=15), end - new_start)

            elif edge == 'bottom':
                # new end, stop at any fixed block above
                new_end = new_time
                for _, fb in self.block_rects:
                    if getattr(fb, "is_fixed", False):
                        fb_start = fb.start
                        fb_end = fb.start + fb.duration
                        # If new_end would overlap fb
                        if start < fb_end and new_end > fb_start:
                            new_end = fb_start  # pull back to avoid collision
                block.duration = max(timedelta(minutes=15), new_end - start)

            self.update()
        elif self.incoming_block:
            # new block being dragged from pool
            duration = timedelta(minutes=self.incoming_block.get("duration", 60))
            y = event.y()
            snapped_y = self.snap_y(y)
            total_minutes = int((snapped_y / self.hour_height) * 60)
            ghost_start = datetime.combine(date.today(), datetime.min.time()) + timedelta(minutes=total_minutes)
            ghost_start = self.find_nearest_non_colliding(ghost_start, duration)
            self.incoming_block['ghost_start'] = ghost_start
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
        if not event.mimeData().hasFormat("application/x-block"):
            return

        event.acceptProposedAction()
        y = event.pos().y()
        snapped_y = self.snap_y(y)
        total_minutes = int((snapped_y / self.hour_height) * 60)

        # --- Existing block being dragged ---
        if self.dragging_block and not getattr(self.dragging_block, "is_fixed", False):
            duration = getattr(self.dragging_block, "duration", timedelta(minutes=60))
            ghost_start = datetime.combine(date.today(), datetime.min.time()) + timedelta(minutes=total_minutes)
            ghost_start = self.find_nearest_non_colliding(ghost_start, duration)
            if ghost_start:
                self.dragging_block.ghost_start = ghost_start
            self.update()

        # --- Incoming block from pool ---
        elif self.incoming_block:
            duration = timedelta(minutes=self.incoming_block.get("duration", 60))
            ghost_start = datetime.combine(date.today(), datetime.min.time()) + timedelta(minutes=total_minutes)
            ghost_start = self.find_nearest_non_colliding(ghost_start, duration)
            if ghost_start:
                self.incoming_block['ghost_start'] = ghost_start
                self.incoming_block['ghost_duration'] = duration
                # ensure it has a name for paintEvent
                if 'name' not in self.incoming_block:
                    self.incoming_block['name'] = "New Block"
            self.update()

    def dropEvent(self, event):
        if not event.mimeData().hasFormat("application/x-block"):
            return

        event.acceptProposedAction()

        # Decode dragged block
        data = pickle.loads(event.mimeData().data("application/x-block"))

        # Compute start time from drop position
        y = event.pos().y()
        snapped_y = self.snap_y(y)
        total_minutes = int((snapped_y / self.hour_height) * 60)
        default_start = datetime.combine(date.today(), datetime.min.time()) + timedelta(minutes=total_minutes)

        block = None

        # --- Custom block ---
        if data.get("is_custom", False):
            # Determine block type for dialog
            block_type = data.get("type", "task")

            # Extract the template from your custom_blocks
            template = next((t for t in self.custom_blocks.templates if t["name"] == data["name"]), {})

            # Build fixed_attrs dictionary
            fixed_attrs = {
                k: v
                for k, v in template.items()
                if k not in ["type"]
            }

            # Open dialog, passing fixed_attrs
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

            # Get variable user data
            user_data = dlg.get_data()

            # Merge fixed attributes with variable data
            merged_data = {**fixed_attrs, **user_data}
            print( merged_data)

            # Instantiate block from template
            block = self.custom_blocks.instantiate(data["name"], **merged_data)


        # --- Default blocks ---
        else:
            block_type = data.get("type", "task")
            if block_type.lower() == "task":
                dlg = AddTaskDialog(utils=self.util, default_start=default_start, parent=self)
                if dlg.exec_() != QDialog.Accepted:
                    self.incoming_block = None
                    self.update()
                    return
                block_data = dlg.get_data()
                start = block_data.get("start") or default_start
                block = task(
                    name=block_data["name"],
                    duration=block_data["duration"],
                    start=start,
                    deadline=block_data["deadline"],
                    location=block_data["location"],
                    notes=block_data["notes"],
                    colour=block_data["colour"]
                )

            elif block_type.lower() == "event":
                dlg = AddEventDialog(utils=self.util, default_start=default_start, parent=self)
                if dlg.exec_() != QDialog.Accepted:
                    self.incoming_block = None
                    self.update()
                    return
                event_data = dlg.get_data()
                block = eventblock(
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
            # Add to schedule
            self.schedule.add_block(block)

            # Refresh DayView
            self.items = self.schedule.day(date.today())
            self.incoming_block = None
            self.update()


    def dragLeaveEvent(self, event):
        self.incoming_block = None
        self.update()  