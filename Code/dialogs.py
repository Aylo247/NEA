from datetime import timedelta, datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QComboBox,
    QDateTimeEdit, QTextEdit, QSpinBox, QDialogButtonBox,
    QColorDialog, QPushButton, QHBoxLayout, QCheckBox,
    QRadioButton, QMessageBox
)
from PyQt5.QtCore import QDateTime
from PyQt5.QtGui import QColor
from typing import Optional

class BaseDialog(QDialog):
    """base dialog for creating or editing a task with name, duration, start, colour, location, and notes"""

    def __init__(
        self, 
        utils, 
        default_start: Optional[datetime] = None, 
        fixed_attrs: Optional[dict] = None,
        parent=None
    ) -> None:
        super().__init__(parent)
        self.utils = utils
        self.fixed_attrs = fixed_attrs or {}

        self.adjustSize()
        self.overall_layout = QVBoxLayout(self)
        self.layout_main = QVBoxLayout(self)
        self.overall_layout.addLayout(self.layout_main)

        # name
        self.layout_main.addWidget(QLabel("name *"))
        self.name_input = QLineEdit()
        self.name_input.setText(self.fixed_attrs.get("name", ""))
        if "name" in self.fixed_attrs:
            self.name_input.setDisabled(True)
        self.layout_main.addWidget(self.name_input)

        # duration
        self.duration_label = QLabel("duration (minutes) *")
        self.layout_main.addWidget(self.duration_label)
        self.duration_input = QSpinBox()
        self.duration_input.setRange(15, 1440)
        self.duration_input.setSingleStep(5)
        self.duration_input.setValue(self.fixed_attrs.get("duration", 60))
        if "duration" in self.fixed_attrs:
            self.duration_input.setDisabled(True)
        self.layout_main.addWidget(self.duration_input)

        # start time (optional)
        self.start_label = QLabel("start time (optional)")
        self.layout_main.addWidget(self.start_label)

        self.start_input = QDateTimeEdit()
        self.start_input.setCalendarPopup(True)
        base_dt = default_start if default_start else datetime.now()
        base_qdt = QDateTime(base_dt) if not isinstance(base_dt, QDateTime) else base_dt
        self.start_input.setDateTime(self.utils.round_qdatetime_to_5(base_qdt))
        self.start_input.setMinimumDateTime(QDateTime.currentDateTime())
        if "start" in self.fixed_attrs:
            self.start_input.setDateTime(QDateTime(self.fixed_attrs["start"]))
            self.start_input.setDisabled(True)
        self.start_input.dateTimeChanged.connect(lambda _: self._snap(self.start_input))
        self.layout_main.addWidget(self.start_input)

        # colour
        self.colour = self.fixed_attrs.get(
            "colour",
            self.utils.tm.get_colour(self.utils.settings.theme, "default_block")
        )
        self.colour = QColor(self.colour) if isinstance(self.colour, str) else self.colour

        self.colour_hex_input = QLineEdit(self.colour.name())
        self.colour_hex_input.setMaxLength(7)
        self.colour_hex_input.setPlaceholderText("#RRGGBB")
        if "colour" in self.fixed_attrs:
            self.colour_hex_input.setDisabled(True)
        self.colour_hex_input.textChanged.connect(self._hex_changed)
        self.layout_main.addWidget(self.colour_hex_input)

        self.colour_button = QPushButton("choose colour")
        if "colour" in self.fixed_attrs:
            self.colour_button.setDisabled(True)
        self.colour_button.clicked.connect(self._open_colour_picker)
        self.layout_main.addWidget(self.colour_button)

        self.colour_dialog = QColorDialog(self.colour, self)
        self.colour_dialog.currentColorChanged.connect(self._colour_picker_changed)

        # location 
        self.location_label = QLabel("location (optional)")
        self.layout_main.addWidget(self.location_label)
        self.location_input = QLineEdit(self.fixed_attrs.get("location", ""))
        if "location" in self.fixed_attrs:
            self.location_input.setDisabled(True)
        self.layout_main.addWidget(self.location_input)

        # notes
        self.notes_label = QLabel("notes (optional)")
        self.layout_main.addWidget(self.notes_label)
        self.notes_input = QTextEdit()
        self.layout_main.addWidget(self.notes_input)

        # buttons 
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.overall_layout.addWidget(buttons)

        # apply theme
        self.utils.apply_theme()

    # helpers
    def _snap(self, widget: QDateTimeEdit) -> None:
        """round the QDateTimeEdit to the nearest 5-minute interval"""
        rounded = self.utils.round_qdatetime_to_5(widget.dateTime())
        if rounded != widget.dateTime():
            widget.blockSignals(True)
            widget.setDateTime(rounded)
            widget.blockSignals(False)

    def _open_colour_picker(self) -> None:
        """open colour picker dialog"""
        if self.colour_dialog.exec_():
            colour = self.colour_dialog.selectedColor()
            if colour.isValid():
                self._set_colour(colour.name())

    def _hex_changed(self, text: str) -> None:
        """update colour from hex input"""
        if QColor.isValidColor(text):
            self._set_colour(text)

    def _set_colour(self, hex_colour) -> None:
        """set colour and update widgets"""
        self.colour = QColor(hex_colour) if isinstance(hex_colour, str) else hex_colour
        self.colour_hex_input.blockSignals(True)
        self.colour_hex_input.setText(self.colour.name())
        self.colour_hex_input.blockSignals(False)
        self.colour_dialog.setCurrentColor(self.colour)

    def _colour_picker_changed(self, colour: QColor) -> None:
        """update colour when colour picker changes"""
        if colour.isValid():
            self._set_colour(colour.name())

    # data 
    def get_data(self) -> dict:
        """return base data (to be extended in subclasses)"""
        data = {
            "name": self.name_input.text().strip(),
            "duration": timedelta(minutes=self.duration_input.value()),
            "start": self.start_input.dateTime().toPyDateTime(),
            "colour": self.colour,
            "location": self.location_input.text().strip() or None,
            "notes": self.notes_input.toPlainText().strip() or None
        }
        if self.fixed_attrs:
            data = {k: v for k, v in data.items() if k not in self.fixed_attrs}
        return data


class AddTaskDialog(BaseDialog):
    """dialog for creating a task with deadline"""

    def __init__(
        self, 
        utils, 
        default_start: Optional[datetime] = None, 
        fixed_attrs: Optional[dict] = None,
        parent=None
    ) -> None:
        super().__init__(utils, default_start, fixed_attrs, parent)
        self.setWindowTitle("add new task")

        layout = self.layout_main  # use the base layout

        # deadline
        layout.addWidget(QLabel("deadline *"))
        self.deadline_input = QDateTimeEdit()
        self.deadline_input.setCalendarPopup(True)
        if "deadline" in self.fixed_attrs:
            base_deadline = self.fixed_attrs["deadline"]
        else:
            start_dt = self.start_input.dateTime().toPyDateTime()
            duration_td = timedelta(minutes=self.duration_input.value())
            base_deadline = start_dt + duration_td
        self.deadline_input.setDateTime(QDateTime(base_deadline))
        if "deadline" in self.fixed_attrs:
            self.deadline_input.setDisabled(True)
        self.deadline_input.dateTimeChanged.connect(lambda _: self._snap(self.deadline_input))
        layout.addWidget(self.deadline_input)

    # data
    def get_data(self) -> dict:
        """return task data including deadline"""
        data = super().get_data()
        data.update({
            "deadline": self.deadline_input.dateTime().toPyDateTime()
        })
        if self.fixed_attrs:
            data = {k: v for k, v in data.items() if k not in self.fixed_attrs}
        return data

    def accept(self) -> None:
        """validate input and accept if valid"""
        errors = []

        if not self.name_input.text().strip():
            errors.append("name cannot be empty,\n imagine if you didnt have one")

        if self.name_input.text().strip().lower() in ["breakfast", "lunch", "dinner", "break"]:
            errors.append(f"name can't be {self.name_input.text.strip()}")

        if self.duration_input.value() <= 0: 
            errors.append("duration must be greater than 0")

        colour = self.colour_hex_input.text().strip()
        if not colour.startswith("#") or len(colour) != 7:
            errors.append("colour must be a valid hex code (e.g., #123ABC),\n or provide an adpt description (the colour\n of her eyes when the sparkle in the sun of the coast... etc.)")

        if errors:
            QMessageBox.warning(self, "oopsie woopsie!", "\n".join(errors))
            return

        super().accept()



class AddEventDialog(BaseDialog):
    """dialog for creating or editing an event, inheriting BaseDialog."""

    def __init__(
        self, 
        utils, 
        default_start: Optional[datetime] = None, 
        fixed_attrs: Optional[dict] = None,
        parent=None
    ) -> None:
        super().__init__(utils, default_start, fixed_attrs, parent)
        self.setWindowTitle("add new event")

        layout = self.layout_main  # use base dialog layout

        # priority
        layout.addWidget(QLabel("priority"))
        self.priority_input = QComboBox()
        self.priority_input.addItems(["0 - Low", "1 - Medium", "2 - High"])
        self.priority_input.setCurrentIndex(self.fixed_attrs.get("priority", 0))
        if "priority" in self.fixed_attrs:
            self.priority_input.setDisabled(True)
        layout.addWidget(self.priority_input)

        # repeatable
        layout.addWidget(QLabel("repeatable?"))
        self.repeatable_input = QComboBox()
        self.repeatable_input.addItems(["No", "Yes"])
        repeatable_value = "Yes" if self.fixed_attrs.get("repeatable", False) else "No"
        self.repeatable_input.setCurrentText(repeatable_value)
        if "repeatable" in self.fixed_attrs:
            self.repeatable_input.setDisabled(True)
        layout.addWidget(self.repeatable_input)

        # interval
        self.interval_label = QLabel("interval (days)")
        self.interval_input = QSpinBox()
        self.interval_input.setRange(1, 28)
        self.interval_input.setValue(self.fixed_attrs.get("interval", 1))
        if "interval" in self.fixed_attrs:
            self.interval_input.setDisabled(True)
        layout.addWidget(self.interval_label)
        layout.addWidget(self.interval_input)

        # show/hide interval depending on repeatable
        self._toggle_interval()
        if "repeatable" not in self.fixed_attrs:
            self.repeatable_input.currentIndexChanged.connect(self._toggle_interval)
        else:
            visible = self.fixed_attrs.get("repeatable", False)
            self.interval_label.setVisible(visible)
            self.interval_input.setVisible(visible)

    # utility methods
    def _toggle_interval(self) -> None:
        """toggles the interval interview"""
        visible = self.repeatable_input.currentText() == "Yes"
        self.interval_label.setVisible(visible)
        self.interval_input.setVisible(visible)

    # data 
    def get_data(self) -> dict:
        data = super().get_data()
        repeatable = self.repeatable_input.currentText() == "Yes"
        data.update({
            "priority": int(self.priority_input.currentText()[0]),
            "repeatable": repeatable,
            "interval": self.interval_input.value() if repeatable else 0
        })
        return data

    def accept(self) -> None:
        """validate input and accept if valid"""
        errors = []

        if not self.name_input.text().strip():
            errors.append("name cannot be empty,\n imagine if you didnt have one")

        if self.name_input.text().strip().lower() in ["breakfast", "lunch", "dinner", "break"]:
            errors.append(f"name can't be {self.name_input.text.strip()}")

        if self.duration_input.value() <= 0: 
            errors.append("duration must be greater than 0")

        colour = self.colour_hex_input.text().strip()
        if not colour.startswith("#") or len(colour) != 7:
            errors.append("colour must be a valid hex code (e.g., #123ABC),\n or provide an adpt description (the colour\n of her eyes when the sparkle in the sun of the coast... etc.)")

        if int(self.priority_input.currentText()[0]) not in [0, 1, 2]:
            errors.append("you really shouln't have got here but\n priority must be 0, 1, or 2")

        if self.interval_input.value() <= 0:
            errors.append("interval must be greater than 0")

        if errors:
            QMessageBox.warning(self, "oopsie woopsie!", "\n".join(errors))
            return

        super().accept()

    

class AddCustomBlockDialog(BaseDialog):
    """dialog for creating a custom task or event block with configurable fields and fixed options"""

    def __init__(self, utils, customs, parent=None) -> None:
        super().__init__(utils, parent=parent)
        self.setWindowTitle("create custom block")
        self.setMinimumWidth(300)
        self.customs = customs

        layout = self.layout_main

        # remove start & notes from BaseDialog
        self.start_label.hide()
        self.start_input.hide()

        self.location_label.hide()

        self.notes_label.hide()
        self.notes_input.hide()

        self.duration_label.hide()

        # block type selector 
        self.type_selector = QComboBox()
        self.type_selector.addItems(["task", "event"])
        self.type_selector.currentIndexChanged.connect(self._switch_form)
        layout.insertWidget(0, QLabel("block type"))
        layout.insertWidget(1, self.type_selector)

        # fixed checkboxes for base fields
        self.duration_fixed = QCheckBox("fixed")
        layout.addLayout(self._make_row("duration (minutes)", self.duration_input, self.duration_fixed))

        self.colour_fixed = QCheckBox("fixed")
        layout.addLayout(self._make_row("colour", self.colour_hex_input, self.colour_fixed, self.colour_button))

        self.location_fixed = QCheckBox("fixed")
        layout.addLayout(self._make_row("location", self.location_input, self.location_fixed))

        # event-only fields with fixed checkboxes
        self.priority_input = QComboBox()
        self.priority_input.addItems(["0 - low", "1 - medium", "2 - high"])
        self.priority_fixed = QCheckBox("fixed")

        self.repeatable_input = QComboBox()
        self.repeatable_input.addItems(["no", "yes"])
        self.repeatable_fixed = QCheckBox("fixed")

        self.interval_input = QSpinBox()
        self.interval_input.setRange(1, 28)
        self.interval_input.setValue(1)
        self.interval_fixed = QCheckBox("fixed")

        self.event_rows = [
            self._make_row("priority", self.priority_input, self.priority_fixed),
            self._make_row("repeatable", self.repeatable_input, self.repeatable_fixed),
            self._make_row("interval (days)", self.interval_input, self.interval_fixed)
        ]
        for row in self.event_rows:
            layout.addLayout(row)

        self._switch_form()  # hide event fields initially if Task

    # utility methods
    def _switch_form(self) -> None:
        """show or hide event-only fields depending on whether the block is a Task or EventBlock."""
        is_task = self.type_selector.currentText() == "task"
        for row in self.event_rows:
            for i in range(row.count()):
                row.itemAt(i).widget().setVisible(not is_task)

    def _make_row(self, label_text, *widgets):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label_text))
        for w in widgets:
            layout.addWidget(w)
        return layout

    # data
    def get_data(self) -> dict:
        """return a dictionary of custom block data, including only fields marked as fixed"""
        data = {
            "type": self.type_selector.currentText().lower(),
            "is_custom": True,
            "name": self.name_input.text().strip() or "New Block"
        }

        # include only fixed fields
        if self.duration_fixed.isChecked():
            data["duration"] = self.duration_input.value()
        if self.colour_fixed.isChecked():
            data["colour"] = self.colour_hex_input.text().strip()
        if self.location_fixed.isChecked():
            data["location"] = self.location_input.text().strip()

        if self.type_selector.currentText() == "event":
            if self.priority_fixed.isChecked():
                data["priority"] = int(self.priority_input.currentText()[0])
            if self.repeatable_fixed.isChecked():
                data["repeatable"] = self.repeatable_input.currentText() == "Yes"
            if self.interval_fixed.isChecked():
                data["interval"] = self.interval_input.value()

        return data

    def accept(self) -> None:
        """validate input and accept if valid"""
        errors = []

        raw_name = self.name_input.text().strip()
        name = raw_name.lower()

        if not name:
            errors.append("name cannot be empty,\n imagine if you didnt have one")

        if name in ["breakfast", "lunch", "dinner", "break"]:
            errors.append(f"name can't be {raw_name}")

        existing_template_names = {
            template.get("name", "").strip().lower()
            for template in self.customs.templates
        }

        if name in existing_template_names:
            errors.append(f"names must be unique\nwheres the creativity?")


        if self.duration_input.value() <= 0: 
            errors.append("duration must be greater than 0")

        colour = self.colour_hex_input.text().strip()
        if not colour.startswith("#") or len(colour) != 7:
            errors.append("colour must be a valid hex code (e.g., #123ABC),\n or provide an adpt description (the colour\n of her eyes when the sparkle in the sun of the coast... etc.)")

        if self.type_selector.currentText() == "event":
            if int(self.priority_input.currentText()[0]) not in [0, 1, 2]:
                errors.append("you really shouln't have got here but\n priority must be 0, 1, or 2")

            if self.interval_input.value() <= 0:
                errors.append("interval must be greater than 0")

        if errors:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "oopsie woopsie!", "\n".join(errors))
            return

        super().accept()

class ClearDayDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Clear schedule")
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Clear schedule for:"))

        self.rest_of_day_radio = QRadioButton("Rest of the day")
        self.hours_radio = QRadioButton("Next number of hours:")
        self.rest_of_day_radio.setChecked(True)

        layout.addWidget(self.rest_of_day_radio)

        hours_row = QHBoxLayout()
        hours_row.addWidget(self.hours_radio)

        self.hours_spin = QSpinBox()
        self.hours_spin.setRange(1, 24)
        self.hours_spin.setValue(1)
        self.hours_spin.setEnabled(False)
        hours_row.addWidget(self.hours_spin)

        layout.addLayout(hours_row)

        # enable spinbox only when needed
        self.hours_radio.toggled.connect(self.hours_spin.setEnabled)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_result(self):
        if self.rest_of_day_radio.isChecked():
            return ("rest_of_day", None)
        return ("hours", self.hours_spin.value())
