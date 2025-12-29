from PyQt5.QtWidgets import QMenu, QDialog
from dialogs import AddTaskDialog, AddEventDialog

class DayViewMenuMixin():
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
