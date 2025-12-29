from datetime import timedelta
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QComboBox,
    QDateTimeEdit, QTextEdit, QSpinBox, QDialogButtonBox,
    QColorDialog, QPushButton
)
from PyQt5.QtCore import QDateTime
from PyQt5.QtGui import QColor


class AddTaskDialog(QDialog):
    def __init__(self, utils, default_start=None, parent=None):
        super().__init__(parent)
        self.utils = utils

        self.setWindowTitle("Add New Task")
        self.resize(300, 400)
        layout = QVBoxLayout(self)

        # --- Name ---
        layout.addWidget(QLabel("Task Name *"))
        self.name_input = QLineEdit()
        layout.addWidget(self.name_input)

        # --- Duration ---
        layout.addWidget(QLabel("Duration (minutes) *"))
        self.duration_input = QSpinBox()
        self.duration_input.setRange(15, 1440)
        self.duration_input.setSingleStep(5)
        self.duration_input.setValue(60)
        layout.addWidget(self.duration_input)

        # --- Deadline ---
        layout.addWidget(QLabel("Deadline *"))
        self.deadline_input = QDateTimeEdit()
        self.deadline_input.setCalendarPopup(True)

        deadline_base = QDateTime.currentDateTime()
        self.deadline_input.setDateTime(
            self.utils.round_qdatetime_to_5(deadline_base)
        )
        layout.addWidget(self.deadline_input)

        # --- Start time (optional) ---
        layout.addWidget(QLabel("Start Time (optional)"))
        self.start_input = QDateTimeEdit()
        self.start_input.setCalendarPopup(True)

        if isinstance(default_start, QDateTime):
            base = default_start
        elif default_start:
            base = QDateTime(default_start)
        else:
            base = QDateTime.currentDateTime()

        self.start_input.setDateTime(
            self.utils.round_qdatetime_to_5(base)
        )
        layout.addWidget(self.start_input)

        self.colour = "#453434"

        self.colour_dialog = QColorDialog(QColor(self.colour), self)
        self.colour_dialog.currentColorChanged.connect(self._colour_picker_changed)

        self.colour_hex_input = QLineEdit(self.colour)
        self.colour_hex_input.setMaxLength(7)
        self.colour_hex_input.setPlaceholderText("#RRGGBB")
        layout.addWidget(self.colour_hex_input)

        self.colour_button = QPushButton("Choose Colour")
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
        self.location_input = QLineEdit()
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
        self.colour = hex_colour
        self.colour_hex_input.blockSignals(True)
        self.colour_hex_input.setText(hex_colour)
        self.colour_hex_input.blockSignals(False)
        self.colour_dialog.setCurrentColor(QColor(hex_colour))

    def _colour_picker_changed(self, colour: QColor):
        if colour.isValid():
            hex_colour = colour.name()
            self.colour = hex_colour

            # update the line edit without triggering textChanged
            self.colour_hex_input.blockSignals(True)
            self.colour_hex_input.setText(hex_colour)
            self.colour_hex_input.blockSignals(False)

    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "duration": timedelta(minutes=self.duration_input.value()),
            "deadline": self.deadline_input.dateTime().toPyDateTime(),
            "colour": self.colour,
            "start": self.start_input.dateTime().toPyDateTime(),
            "location": self.location_input.text().strip() or None,
            "notes": self.notes_input.toPlainText().strip() or None,
        }

class AddEventDialog(QDialog):
    def __init__(self, utils, default_start=None, parent=None):
        super().__init__(parent)
        self.utils = utils

        self.setWindowTitle("Add New Event")
        self.resize(300, 500)
        layout = QVBoxLayout(self)

        # --- Name ---
        layout.addWidget(QLabel("Event Name *"))
        self.name_input = QLineEdit()
        layout.addWidget(self.name_input)

        # --- Duration ---
        layout.addWidget(QLabel("Duration (minutes) *"))
        self.duration_input = QSpinBox()
        self.duration_input.setRange(15, 1440)
        self.duration_input.setSingleStep(5)
        self.duration_input.setValue(60)
        layout.addWidget(self.duration_input)

        # --- Start time ---
        layout.addWidget(QLabel("Start Time *"))
        self.start_input = QDateTimeEdit()
        self.start_input.setCalendarPopup(True)

        self.colour = self.utils.tm.get_colour(self.utils.settings.theme, "default_block")

        self.colour_dialog = QColorDialog(QColor(self.colour), self)
        self.colour_dialog.currentColorChanged.connect(self._colour_picker_changed)

        self.colour_hex_input = QLineEdit(self.colour)
        self.colour_hex_input.setMaxLength(7)
        self.colour_hex_input.setPlaceholderText("#RRGGBB")
        layout.addWidget(self.colour_hex_input)

        self.colour_button = QPushButton("Choose Colour")
        layout.addWidget(self.colour_button)
        self.colour_button.clicked.connect(self._open_colour_picker)


        if isinstance(default_start, QDateTime):
            base = default_start
        elif default_start:
            base = QDateTime(default_start)
        else:
            base = QDateTime.currentDateTime()

        self.start_input.setDateTime(
            self.utils.round_qdatetime_to_5(base)
        )
        layout.addWidget(self.start_input)

        self.start_input.dateTimeChanged.connect(
            lambda _: self._snap(self.start_input)
        )

        # --- Priority ---
        layout.addWidget(QLabel("Priority"))
        self.priority_input = QComboBox()
        self.priority_input.addItems(["0 - Low", "1 - Medium", "2 - High"])
        self.priority_input.setCurrentIndex(0)
        layout.addWidget(self.priority_input)

        # --- Repeatable ---
        layout.addWidget(QLabel("Repeatable?"))
        self.repeatable_input = QComboBox()
        self.repeatable_input.addItems(["No", "Yes"])
        layout.addWidget(self.repeatable_input)

        # --- Interval ---
        self.interval_label = QLabel("Interval (days)")
        self.interval_input = QSpinBox()
        self.interval_input.setRange(1, 28)
        self.interval_input.setValue(1)
        layout.addWidget(self.interval_label)
        layout.addWidget(self.interval_input)

        self.interval_label.hide()
        self.interval_input.hide()

        self.repeatable_input.currentIndexChanged.connect(
            self._toggle_interval
        )

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
        self.colour = hex_colour
        self.colour_hex_input.blockSignals(True)
        self.colour_hex_input.setText(hex_colour)
        self.colour_hex_input.blockSignals(False)
        self.colour_dialog.setCurrentColor(QColor(hex_colour))

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

        return {
            "name": self.name_input.text().strip() or "New Event",
            "duration": timedelta(minutes=self.duration_input.value()),
            "start": self.start_input.dateTime().toPyDateTime(),
            "colour": self.colour,
            "priority": int(self.priority_input.currentText()[0]),
            "repeatable": repeatable,
            "interval": self.interval_input.value() if repeatable else 0,
        }
