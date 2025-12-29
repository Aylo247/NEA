from PyQt5.QtWidgets import QMenu, QDialog
from dialogs import AddTaskDialog, AddEventDialog

class DayViewMenuMixin():
    def show_block_menu(self, block, global_pos):
        if getattr(block, "name", "").lower() in ["break", "breakfast", "lunch", "dinner"]:
            return

        menu = QMenu(self)
        menu.addAction("Edit", lambda b=block: self.edit_block(b))
        menu.addAction("Delete", lambda b=block: self.delete_block(b))
        menu.addAction("Inspect", lambda b=block: self.inspect_block(b))

        # Mark as done/undone for tasks
        if getattr(block, "type", None) == "task":
            done_text = "Mark as Undone" if getattr(block, "is_completed", False) else "Mark as Done"
            menu.addAction(done_text, lambda b=block: self.toggle_task_done(b))

        menu.exec_(global_pos)

    def edit_block(self, block):
        if getattr(block, "type", None) == "task":
            dialog = AddTaskDialog(self.util, default_start=block.start, parent=self)
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
                self.schedule.global_edf_scheduler()
                self.update()

        elif getattr(block, "type", None) == "event":
            dialog = AddEventDialog(self.util, default_start=block.start, parent=self)
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
                self.schedule.global_edf_scheduler()
                self.update()

    def delete_block(self, block):
        self.schedule.remove_block(block)
        self.update()

    def toggle_task_done(self, block):
        if getattr(block, "is_completed", False):
            self.schedule.mark_incomplete(block)
        else:
            self.schedule.mark_complete(block)
        self.update()
