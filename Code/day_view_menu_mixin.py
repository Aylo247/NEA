from PyQt5.QtWidgets import (
    QMenu, QDialog, QHBoxLayout, QVBoxLayout,
    QLabel, QDialogButtonBox
    )
from dialogs import AddTaskDialog, AddEventDialog
from datetime import timedelta

class DayViewMenuMixin:
    """mixin providing context menu functionality for blocks in a DayView"""

    def show_block_menu(self, block, global_pos) -> None:
        """
        display a context menu for a block with options to edit, delete, inspect,
        or mark task as done/undone
        """
        # skip meals/breaks
        if getattr(block, "name", "").lower() in ["break", "breakfast", "lunch", "dinner"]:
            return

        menu = QMenu(self)
        menu.addAction("edit", lambda b=block: self.edit_block(b))
        menu.addAction("delete", lambda b=block: self.delete_block(b))
        menu.addAction("inspect", lambda b=block: self.inspect_block(b))

        if getattr(block, "type", None) == "task":
            done_text = "mark as undone" if getattr(block, "is_completed", False) else "mark as done"
            menu.addAction(done_text, lambda b=block: self.toggle_task_done(b))

        menu.exec_(global_pos)

    def edit_block(self, block) -> None:
        """open an edit dialog and update the real block in schedule"""
        # make sure block is the actual object in the schedule
        real_block = block

        if getattr(real_block, "type", None) == "task":
            dialog = AddTaskDialog(self.util, default_start=real_block.start, parent=self)
            dialog.name_input.setText(real_block.name)
            dialog.duration_input.setValue(int(real_block.duration.total_seconds() // 60))
            if real_block.deadline:
                dialog.deadline_input.setDateTime(real_block.deadline)
            if real_block.location:
                dialog.location_input.setText(real_block.location)
            if real_block.notes:
                dialog.notes_input.setText(real_block.notes)

            if dialog.exec_() == QDialog.Accepted:
                data = dialog.get_data()

                # ensure correct types
                real_block.name = data["name"]
                real_block.start = data["start"]
                real_block.duration = data["duration"] if isinstance(data["duration"], timedelta) else timedelta(minutes=int(data["duration"]))
                real_block.deadline = data.get("deadline")
                real_block.location = data.get("location")
                real_block.notes = data.get("notes")

                print(f"[DEBUG] Edited block: {real_block.name}, {real_block.start}, {real_block.duration}")
                self.schedule.global_edf_scheduler(ignore_blocks=[real_block])  # recalc schedule
                self.update()

        elif getattr(real_block, "type", None) == "event":
            dialog = AddEventDialog(self.util, default_start=real_block.start, parent=self)
            dialog.name_input.setText(real_block.name)
            dialog.duration_input.setValue(int(real_block.duration.total_seconds() // 60))
            dialog.priority_input.setCurrentIndex(getattr(real_block, "priority", 0))
            repeatable = getattr(real_block, "repeatable", False)
            dialog.repeatable_input.setCurrentIndex(1 if repeatable else 0)
            dialog.interval_input.setValue(getattr(real_block, "interval", 1))

            if dialog.exec_() == QDialog.Accepted:
                data = dialog.get_data()
                real_block.name = data["name"]
                real_block.start = data["start"]
                real_block.duration = data["duration"] if isinstance(data["duration"], timedelta) else timedelta(minutes=int(data["duration"]))
                real_block.priority = data.get("priority", 0)
                real_block.repeatable = data.get("repeatable", False)
                real_block.interval = data.get("interval", 1)

                print(f"[DEBUG] Edited event: {real_block.name}, {real_block.start}, {real_block.duration}")
                self.schedule.global_edf_scheduler()
                self.update()

    def delete_block(self, block) -> None:
        """remove the real block from schedule"""
        real_block = block
        self.schedule.remove_block(real_block)
        print(f"[DEBUG] Deleted block: {real_block.name}")
        self.update()

    def toggle_task_done(self, block) -> None:
        """toggle completion for the real task block"""
        real_block = block
        if getattr(real_block, "is_completed", False):
            self.schedule.mark_incomplete(real_block)
            print(f"[DEBUG] Marked undone: {real_block.name}")
        else:
            self.schedule.mark_complete(real_block)
            print(f"[DEBUG] Marked done: {real_block.name}")
        self.update()

    def inspect_block(self, block) -> None:
        """show a read-only dialog with all block details"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Block Details")
        dialog.setModal(True)

        layout = QVBoxLayout(dialog)

        def add_row(label, value):
            row = QHBoxLayout()
            row.addWidget(QLabel(f"<b>{label}:</b>"))
            row.addWidget(QLabel(value))
            layout.addLayout(row)

        # Common fields
        add_row("Name", block.name)
        add_row("Type", block.type.capitalize())
        add_row("Start", block.start.strftime("%Y-%m-%d %H:%M"))
        add_row("Duration", f"{int(block.duration.total_seconds() // 60)} minutes")

        if getattr(block, "location", None):
            add_row("Location", block.location)

        if getattr(block, "notes", None):
            add_row("Notes", block.notes)

        if getattr(block, "colour", None):
            add_row("Colour", str(block.colour))

        # Task-specific
        if block.type == "task":
            add_row(
                "Deadline",
                block.deadline.strftime("%Y-%m-%d %H:%M") if block.deadline else "None"
            )
            add_row("Completed", "Yes" if block.is_completed else "No")
            if block.is_completed and block.completed_at:
                add_row("Completed At", block.completed_at.strftime("%Y-%m-%d %H:%M"))

        # Event-specific
        if block.type == "event":
            add_row("Priority", str(block.priority))
            add_row("Repeatable", "Yes" if block.repeatable else "No")
            if block.repeatable:
                add_row("Interval", f"{block.interval} days")

        # OK button
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)

        dialog.exec_()

