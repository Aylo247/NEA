from datetime import timedelta
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QComboBox,
    QDateTimeEdit, QTextEdit, QSpinBox, QDialogButtonBox,
    QColorDialog, QPushButton, QHBoxLayout, QCheckBox,
    QSizePolicy
)
from PyQt5.QtCore import QDateTime
from PyQt5.QtGui import QColor


class AddTaskDialog(QDialog):
    def __init__(self, utils, default_start=None, fixed_attrs = None, parent=None):
        super().__init__(parent)
        self.utils = utils
        self.fixed_attrs = fixed_attrs or {}

        self.setWindowTitle("Add New Task")
        self.resize(300, 400)
        layout = QVBoxLayout(self)

        # --- Name ---
        layout.addWidget(QLabel("Task Name *"))
        self.name_input = QLineEdit()
        self.name_input.setText(self.fixed_attrs.get("name", ""))
        if "name" in self.fixed_attrs:
            self.name_input.setDisabled(True)
        layout.addWidget(self.name_input)

        # --- Duration ---
        layout.addWidget(QLabel("Duration (minutes) *"))
        self.duration_input = QSpinBox()
        self.duration_input.setRange(15, 1440)
        self.duration_input.setSingleStep(5)
        self.duration_input.setValue(self.fixed_attrs.get("duration", 60))
        if "duration" in self.fixed_attrs:
            self.duration_input.setDisabled(True)
        layout.addWidget(self.duration_input)

        # --- Start time (optional) ---
        layout.addWidget(QLabel("Start Time (optional)"))
        self.start_input = QDateTimeEdit()
        self.start_input.setCalendarPopup(True)
        if default_start:
            base = QDateTime(default_start) if not isinstance(default_start, QDateTime) else default_start
        else:
            base = QDateTime.currentDateTime()
        self.start_input.setDateTime(self.utils.round_qdatetime_to_5(base))
        if "start" in self.fixed_attrs:
            self.start_input.setDateTime(QDateTime(self.fixed_attrs["start"]))
            self.start_input.setDisabled(True)
        layout.addWidget(self.start_input)

        # --- Deadline ---
        layout.addWidget(QLabel("Deadline *"))
        self.deadline_input = QDateTimeEdit()
        self.deadline_input.setCalendarPopup(True)

        # Determine base deadline
        if "deadline" in self.fixed_attrs:
            base_deadline = self.fixed_attrs["deadline"]
        else:
            # Ensure deadline is at least start + duration
            start_dt = self.start_input.dateTime().toPyDateTime()
            duration_td = timedelta(minutes=self.duration_input.value())
            base_deadline = start_dt + duration_td

        self.deadline_input.setDateTime(QDateTime(base_deadline))

        # Disable if fixed
        if "deadline" in self.fixed_attrs:
            self.deadline_input.setDisabled(True)

        layout.addWidget(self.deadline_input)

        # --- Colour ---
        self.colour = self.fixed_attrs.get(
            "colour", 
            self.utils.tm.get_colour(self.utils.settings.theme, "default_block")
        )
        self.colour_dialog = QColorDialog(QColor(self.colour), self)
        self.colour_dialog.currentColorChanged.connect(self._colour_picker_changed)

        self.colour = QColor(self.colour) if isinstance(self.colour, str) else self.colour
        self.colour_hex_input = QLineEdit(self.colour.name())
        self.colour_hex_input.setMaxLength(7)
        self.colour_hex_input.setPlaceholderText("#RRGGBB")
        if "colour" in self.fixed_attrs:
            self.colour_hex_input.setDisabled(True)
        layout.addWidget(self.colour_hex_input)

        self.colour_button = QPushButton("Choose Colour")
        if "colour" in self.fixed_attrs:
            self.colour_button.setDisabled(True)
        layout.addWidget(self.colour_button)
        self.colour_button.clicked.connect(self._open_colour_picker)

        # Live snapping
        self.deadline_input.dateTimeChanged.connect(
            lambda _: self._snap(self.deadline_input)
        )
        self.start_input.dateTimeChanged.connect(
            lambda _: self._snap(self.start_input)
        )

        # --- Location ---
        layout.addWidget(QLabel("Location (optional)"))
        self.location_input = QLineEdit(self.fixed_attrs.get("location", ""))
        if "location" in self.fixed_attrs:
            self.location_input.setDisabled(True)
        layout.addWidget(self.location_input)

        # --- Notes ---
        layout.addWidget(QLabel("Notes (optional)"))
        self.notes_input = QTextEdit()
        layout.addWidget(self.notes_input)

        # --- Buttons ---
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

    def _snap(self, widget: QDateTimeEdit):
        rounded = self.utils.round_qdatetime_to_5(widget.dateTime())
        if rounded != widget.dateTime():
            widget.blockSignals(True)
            widget.setDateTime(rounded)
            widget.blockSignals(False)

    def _open_colour_picker(self):
        if self.colour_dialog.exec_():
            colour = self.colour_dialog.selectedColor()
            if colour.isValid():
                self._set_colour(colour.name())

    def _hex_changed(self, text):
        if QColor.isValidColor(text):
            self._set_colour(text)

    def _set_colour(self, hex_colour):
        # Ensure self.colour is always a QColor
        self.colour = QColor(hex_colour) if isinstance(hex_colour, str) else hex_colour

        # Update the line edit with a string
        self.colour_hex_input.blockSignals(True)
        self.colour_hex_input.setText(self.colour.name())  # <-- use .name() to get "#RRGGBB"
        self.colour_hex_input.blockSignals(False)

        # Update the QColorDialog
        self.colour_dialog.setCurrentColor(self.colour)


    def _colour_picker_changed(self, colour: QColor):
        if colour.isValid():
            self.colour = colour  # store as QColor

            # update the line edit without triggering textChanged
            self.colour_hex_input.blockSignals(True)
            self.colour_hex_input.setText(colour.name())  # string for QLineEdit
            self.colour_hex_input.blockSignals(False)

    def get_data(self):
        data = {
            "name": self.name_input.text().strip(),
            "duration": timedelta(minutes=self.duration_input.value()),
            "deadline": self.deadline_input.dateTime().toPyDateTime(),
            "colour": self.colour,
            "start": self.start_input.dateTime().toPyDateTime(),
            "location": self.location_input.text().strip() or None,
            "notes": self.notes_input.toPlainText().strip() or None,
        }

        # Only include keys that are not fixed
        if hasattr(self, 'fixed_attrs') and self.fixed_attrs:
            data = {k: v for k, v in data.items() if k not in self.fixed_attrs}

        return data

class AddEventDialog(QDialog):
    def __init__(self, utils, default_start=None, fixed_attrs=None, parent=None):
        super().__init__(parent)
        self.utils = utils
        self.fixed_attrs = fixed_attrs or {}

        self.setWindowTitle("Add New Event")
        self.resize(300, 500)
        layout = QVBoxLayout(self)

        # --- Name ---
        layout.addWidget(QLabel("Event Name *"))
        self.name_input = QLineEdit(self.fixed_attrs.get("name", ""))
        if "name" in self.fixed_attrs:
            self.name_input.setDisabled(True)
        layout.addWidget(self.name_input)

        # --- Duration ---
        layout.addWidget(QLabel("Duration (minutes) *"))
        self.duration_input = QSpinBox()
        self.duration_input.setRange(15, 1440)
        self.duration_input.setSingleStep(5)
        self.duration_input.setValue(self.fixed_attrs.get("duration", 60))
        if "duration" in self.fixed_attrs:
            self.duration_input.setDisabled(True)
        layout.addWidget(self.duration_input)

        # --- Start time ---
        layout.addWidget(QLabel("Start Time *"))
        self.start_input = QDateTimeEdit()
        self.start_input.setCalendarPopup(True)
        if default_start:
            base = QDateTime(default_start) if not isinstance(default_start, QDateTime) else default_start
        else:
            base = QDateTime.currentDateTime()
        start_value = self.fixed_attrs.get("start", base.toPyDateTime())
        self.start_input.setDateTime(self.utils.round_qdatetime_to_5(QDateTime(start_value)))
        if "start" in self.fixed_attrs:
            self.start_input.setDisabled(True)
        layout.addWidget(self.start_input)

        self.start_input.dateTimeChanged.connect(lambda _: self._snap(self.start_input))

        # --- Colour ---
        self.colour = self.fixed_attrs.get(
            "colour", 
            self.utils.tm.get_colour(self.utils.settings.theme, "default_block")
        )
        self.colour_dialog = QColorDialog(QColor(self.colour), self)
        self.colour_dialog.currentColorChanged.connect(self._colour_picker_changed)

        self.colour = QColor(self.colour) if isinstance(self.colour, str) else self.colour
        self.colour_hex_input = QLineEdit(self.colour.name())
        self.colour_hex_input.setMaxLength(7)
        self.colour_hex_input.setPlaceholderText("#RRGGBB")
        if "colour" in self.fixed_attrs:
            self.colour_hex_input.setDisabled(True)
        layout.addWidget(self.colour_hex_input)

        self.colour_button = QPushButton("Choose Colour")
        if "colour" in self.fixed_attrs:
            self.colour_button.setDisabled(True)
        layout.addWidget(self.colour_button)
        self.colour_button.clicked.connect(self._open_colour_picker)

        # --- Priority ---
        layout.addWidget(QLabel("Priority"))
        self.priority_input = QComboBox()
        self.priority_input.addItems(["0 - Low", "1 - Medium", "2 - High"])
        priority_value = self.fixed_attrs.get("priority", 0)
        self.priority_input.setCurrentIndex(priority_value)
        if "priority" in self.fixed_attrs:
            self.priority_input.setDisabled(True)
        layout.addWidget(self.priority_input)

        # --- Repeatable ---
        layout.addWidget(QLabel("Repeatable?"))
        self.repeatable_input = QComboBox()
        self.repeatable_input.addItems(["No", "Yes"])
        repeatable_value = "Yes" if self.fixed_attrs.get("repeatable", False) else "No"
        self.repeatable_input.setCurrentText(repeatable_value)
        if "repeatable" in self.fixed_attrs:
            self.repeatable_input.setDisabled(True)
        layout.addWidget(self.repeatable_input)

        # --- Interval ---
        self.interval_label = QLabel("Interval (days)")
        self.interval_input = QSpinBox()
        self.interval_input.setRange(1, 28)
        self.interval_input.setValue(self.fixed_attrs.get("interval", 1))
        if "interval" in self.fixed_attrs:
            self.interval_input.setDisabled(True)
        layout.addWidget(self.interval_label)
        layout.addWidget(self.interval_input)

        self._toggle_interval()  # adjust visibility based on repeatable
        if "repeatable" in self.fixed_attrs:
            self.interval_label.setVisible(self.fixed_attrs.get("repeatable", False))
            self.interval_input.setVisible(self.fixed_attrs.get("repeatable", False))
        else:
            self.repeatable_input.currentIndexChanged.connect(self._toggle_interval)

        # --- Location ---
        layout.addWidget(QLabel("Location (optional)"))
        self.location_input = QLineEdit(self.fixed_attrs.get("location", ""))
        if "location" in self.fixed_attrs:
            self.location_input.setDisabled(True)
        layout.addWidget(self.location_input)

        # --- Notes ---
        layout.addWidget(QLabel("Notes (optional)"))
        self.notes_input = QTextEdit()
        layout.addWidget(self.notes_input)

        # --- Buttons ---
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

    def _snap(self, widget: QDateTimeEdit):
        rounded = self.utils.round_qdatetime_to_5(widget.dateTime())
        if rounded != widget.dateTime():
            widget.blockSignals(True)
            widget.setDateTime(rounded)
            widget.blockSignals(False)

    def _toggle_interval(self):
        visible = self.repeatable_input.currentText() == "Yes"
        self.interval_label.setVisible(visible)
        self.interval_input.setVisible(visible)

    def _open_colour_picker(self):
        if self.colour_dialog.exec_():
            colour = self.colour_dialog.selectedColor()
            if colour.isValid():
                self._set_colour(colour.name())

    def _hex_changed(self, text):
        if QColor.isValidColor(text):
            self._set_colour(text)

    def _set_colour(self, hex_colour):
        # Ensure self.colour is always a QColor
        self.colour = QColor(hex_colour) if isinstance(hex_colour, str) else hex_colour

        # Update the line edit with a string
        self.colour_hex_input.blockSignals(True)
        self.colour_hex_input.setText(self.colour.name())  # <-- use .name() to get "#RRGGBB"
        self.colour_hex_input.blockSignals(False)

        # Update the QColorDialog
        self.colour_dialog.setCurrentColor(self.colour)

    def _colour_picker_changed(self, colour: QColor):
        if colour.isValid():
            hex_colour = colour.name()
            self.colour = hex_colour

            # update the line edit without triggering textChanged
            self.colour_hex_input.blockSignals(True)
            self.colour_hex_input.setText(hex_colour)
            self.colour_hex_input.blockSignals(False)

    def get_data(self):
        repeatable = self.repeatable_input.currentText() == "Yes"

        data = {
            "name": self.name_input.text().strip() or "New Event",
            "duration": timedelta(minutes=self.duration_input.value()),
            "start": self.start_input.dateTime().toPyDateTime(),
            "colour": self.colour,
            "priority": int(self.priority_input.currentText()[0]),
            "repeatable": repeatable,
            "interval": self.interval_input.value() if repeatable else 0,
            "location": self.location_input.text().strip() or None,
            "notes": self.notes_input.toPlainText().strip() or None,
        }

        # Remove fixed attributes so they stay as per template
        if hasattr(self, 'fixed_attrs') and self.fixed_attrs:
            data = {k: v for k, v in data.items() if k not in self.fixed_attrs}

        return data
    

class AddCustomBlockDialog(QDialog):
    def __init__(self, utils, parent=None):
        super().__init__(parent)
        self.utils = utils
        self.setWindowTitle("Create Custom Block")
        self.setMinimumWidth(300)

        self.layout_main = QVBoxLayout(self)

       # --- Block type selector ---
        hl = QHBoxLayout()
        label = QLabel("Block Type")
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # prevent it from expanding
        hl.addWidget(label)
        hl.addStretch()  # pushes the label to the left without extra vertical space
        self.layout_main.addLayout(hl)

        self.type_selector = QComboBox()
        self.type_selector.addItems(["Task", "Event"])
        self.type_selector.currentIndexChanged.connect(self._switch_form)
        self.layout_main.addWidget(self.type_selector)

        # --- Name (always required) ---
        self.name_input = QLineEdit()
        self.layout_main.addLayout(self._make_row("Name", self.name_input))

        # --- Duration ---
        self.duration_input = QSpinBox()
        self.duration_input.setRange(15, 1440)
        self.duration_input.setSingleStep(5)
        self.duration_input.setValue(60)
        self.duration_fixed = QCheckBox("Fixed")
        self.layout_main.addLayout(self._make_row("Duration (minutes)", self.duration_input, self.duration_fixed))

        # --- Colour ---
        self.colour = "#453434"
        self.colour_input = QLineEdit(self.colour)
        self.colour_fixed = QCheckBox("Fixed")
        self.colour_button = QPushButton("Choose Colour")
        self.colour_button.clicked.connect(self._open_colour_picker)
        self.colour_dialog = QColorDialog(QColor(self.colour), self)
        self.colour_dialog.currentColorChanged.connect(self._colour_picker_changed)
        self.layout_main.addLayout(self._make_row("Colour", self.colour_input, self.colour_fixed, self.colour_button))

        # --- Location ---
        self.location_input = QLineEdit()
        self.location_fixed = QCheckBox("Fixed")
        self.layout_main.addLayout(self._make_row("Location", self.location_input, self.location_fixed))

        # --- Event-only fields ---
        self.priority_input = QComboBox()
        self.priority_input.addItems(["0 - Low", "1 - Medium", "2 - High"])
        self.priority_fixed = QCheckBox("Fixed")
        self.repeatable_input = QComboBox()
        self.repeatable_input.addItems(["No", "Yes"])
        self.repeatable_fixed = QCheckBox("Fixed")
        self.interval_input = QSpinBox()
        self.interval_input.setRange(1, 28)
        self.interval_input.setValue(1)
        self.interval_fixed = QCheckBox("Fixed")

        self.event_rows = [
            self._make_row("Priority", self.priority_input, self.priority_fixed),
            self._make_row("Repeatable", self.repeatable_input, self.repeatable_fixed),
            self._make_row("Interval (days)", self.interval_input, self.interval_fixed)
        ]
        for row in self.event_rows:
            self.layout_main.addLayout(row)

        # Initially hide event fields if Task
        self._switch_form()

        # --- Buttons ---
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout_main.addWidget(buttons)

    def _make_row(self, label_text, *widgets):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label_text))
        for w in widgets:
            layout.addWidget(w)
        return layout

    def _switch_form(self):
        is_task = self.type_selector.currentText() == "Task"
        for row in self.event_rows:
            for i in range(row.count()):
                row.itemAt(i).widget().setVisible(not is_task)

    def _open_colour_picker(self):
        if self.colour_dialog.exec_():
            colour = self.colour_dialog.selectedColor()
            if colour.isValid():
                self._set_colour(colour.name())

    def _hex_changed(self, text):
        if QColor.isValidColor(text):
            self._set_colour(text)

    def _set_colour(self, hex_colour):
        # Ensure self.colour is always a QColor
        self.colour = QColor(hex_colour) if isinstance(hex_colour, str) else hex_colour

        # Update the line edit with a string
        self.colour_hex_input.blockSignals(True)
        self.colour_hex_input.setText(self.colour.name())  # <-- use .name() to get "#RRGGBB"
        self.colour_hex_input.blockSignals(False)

        # Update the QColorDialog
        self.colour_dialog.setCurrentColor(self.colour)

    def _colour_picker_changed(self, colour: QColor):
        if colour.isValid():
            self.colour = colour  # store as QColor

            # update the line edit without triggering textChanged
            self.colour_hex_input.blockSignals(True)
            self.colour_hex_input.setText(colour.name())  # string for QLineEdit
            self.colour_hex_input.blockSignals(False)

    def get_data(self):
        """Return block data, including only fixed fields."""
        data = {
            "type": self.type_selector.currentText().lower(),
            "is_custom": True
        }

        # Only add fields if the checkbox is checked
        if self.name_input.text().strip():  # name is always included
            data["name"] = self.name_input.text().strip()
        
        if self.duration_fixed.isChecked():
            data["duration"] = self.duration_input.value()
        if self.colour_fixed.isChecked():
            data["colour"] = self.colour_input.text().strip()
        if self.location_fixed.isChecked():
            data["location"] = self.location_input.text().strip()

        # Event-only
        if self.type_selector.currentText() == "Event":
            if self.priority_fixed.isChecked():
                data["priority"] = int(self.priority_input.currentText()[0])
            if self.repeatable_fixed.isChecked():
                data["repeatable"] = self.repeatable_input.currentText() == "Yes"
            if self.interval_fixed.isChecked():
                data["interval"] = self.interval_input.value()

        return data


    
    def accept(self):
        errors = []

        # Name must not be empty
        if not self.name_input.text().strip():
            errors.append("name cannot be empty.")

        # Duration must be positive
        if self.duration_input.value() <= 0:
            errors.append("duration must be greater than 0.")

        # Colour must be a valid hex
        colour = self.colour_input.text().strip()
        if not colour.startswith("#") or len(colour) != 7:
            errors.append("colour must be a valid hex code (e.g., #123ABC).")

        # Event-only validations
        if self.type_selector.currentText() == "Event":
            if int(self.priority_input.currentText()[0]) not in [0, 1, 2]:
                errors.append("priority must be 0, 1, or 2, oh, it must i promise you")
            if self.interval_input.value() <= 0:
                errors.append("interval must be greater than 0.")

        if errors:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "oopsie woopsie", "\n".join(errors))
            return  # don’t close the dialog

        # All good → call original accept
        super().accept()



