from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QFormLayout, QComboBox, 
    QPushButton, QMessageBox, QDialog, QCalendarWidget, QListWidget, 
    QHBoxLayout, QSpinBox, QListWidgetItem
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import (
    QTime, QDate, pyqtSignal, QDateTime
)
import copy
from datetime import timedelta
from utils import FiveMinuteTimeEdit

class SettingsView(QWidget):
    """setting view allowing for editing of settings"""
    back = pyqtSignal()

    def __init__(self, settings, persistence_manager, util) -> None:
        super().__init__()

        self.settings = settings
        self.persistence = persistence_manager
        self.util = util        

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # top bar 
        top_bar, buttons = self.util.create_top_bar(show_back=True)
        buttons["back"].clicked.connect(self.on_back_clicked)
        self.main_layout.addWidget(top_bar)

        # general settings
        self.general_group = QGroupBox("general settings")
        self.general_form = QFormLayout()
        self.general_group.setLayout(self.general_form)
        self.main_layout.addWidget(self.general_group)

        # theme selection
        self.theme_box = QComboBox()
        self.theme_box.addItems(["light", "dark"])
        self.theme_box.setCurrentText(self.settings.theme)
        self.theme_box.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.theme_box.setMinimumWidth(100)
        self.general_form.addRow("theme", self.theme_box)

        # weekday times
        self.start_time_edit = FiveMinuteTimeEdit(QTime(self.settings.start_time.hour, self.settings.start_time.minute))
        self.end_time_edit = FiveMinuteTimeEdit(QTime(self.settings.end_time.hour, self.settings.end_time.minute))
        self.general_form.addRow("weekday start time", self.start_time_edit)
        self.general_form.addRow("weekday end time", self.end_time_edit)
        self.start_time_edit.timeChanged.connect(self.validate_weekday_times)
        self.end_time_edit.timeChanged.connect(self.validate_weekday_times)

        # weekend times
        self.weekend_start_edit = FiveMinuteTimeEdit(QTime(self.settings.weekend_start.hour, self.settings.weekend_start.minute))
        self.weekend_end_edit = FiveMinuteTimeEdit(QTime(self.settings.weekend_end.hour, self.settings.weekend_end.minute))
        self.general_form.addRow("weekend start time", self.weekend_start_edit)
        self.general_form.addRow("weekend end time", self.weekend_end_edit)
        self.weekend_start_edit.timeChanged.connect(self.validate_weekend_times)
        self.weekend_end_edit.timeChanged.connect(self.validate_weekend_times)

        # break duration
        self.break_duration_spin = QSpinBox()
        self.break_duration_spin.setRange(5, 120)  # minutes
        self.break_duration_spin.setSuffix(" min")
        self.break_duration_spin.setValue(int(self.settings.break_duration.total_seconds() // 60))
        self.break_duration_spin.setSingleStep(5)
        self.break_duration_spin.valueChanged.connect(self.on_break_duration_changed)
        self.general_form.addRow("break duration", self.break_duration_spin)

        # break interval
        self.break_interval_spin = QSpinBox()
        self.break_interval_spin.setRange(30, 240)
        self.break_interval_spin.setSingleStep(5)
        self.break_interval_spin.setSuffix(" min")
        self.break_interval_spin.setValue(int(self.settings.break_interval.total_seconds() // 60))
        self.break_interval_spin.valueChanged.connect(self.on_break_interval_changed)
        self.general_form.addRow("break interval", self.break_interval_spin)

        # notification duration
        self.notification_spin = QSpinBox()
        self.notification_spin.setRange(1, 120)  # minutes
        self.notification_spin.setSuffix(" min")
        self.notification_spin.setValue(int(self.settings.notification_frequency.total_seconds() // 60))
        self.notification_spin.setSingleStep(5)
        self.notification_spin.valueChanged.connect(self.on_notification_duration_changed)
        self.general_form.addRow("notification duration", self.notification_spin)

        # meal settings
        self.meal_group = QGroupBox("meal times")
        self.meal_form = QFormLayout()
        self.meal_group.setLayout(self.meal_form)
        self.main_layout.addWidget(self.meal_group)

        self.meal_edits = {}
        for meal, (start, end) in self.settings.meal_windows.items():
            start_edit = FiveMinuteTimeEdit(QTime(start.hour, start.minute))
            end_edit = FiveMinuteTimeEdit(QTime(end.hour, end.minute))
            start_edit.timeChanged.connect(self.validate_meal_times)
            end_edit.timeChanged.connect(self.validate_meal_times)
            self.meal_form.addRow(f"{meal} start".lower(), start_edit)
            self.meal_form.addRow(f"{meal} end".lower(), end_edit)
            self.meal_edits[meal] = (start_edit, end_edit)

        # meal duration
        self.meal_duration_spin = QSpinBox()
        self.meal_duration_spin.setRange(15, 120)
        self.meal_duration_spin.setSingleStep(5)
        self.meal_duration_spin.setSuffix(" min")
        self.meal_duration_spin.setValue(int(self.settings.meal_duration.total_seconds() // 60))
        self.meal_duration_spin.valueChanged.connect(self.on_meal_duration_changed)
        self.meal_form.addRow("meal duration", self.meal_duration_spin)

        # holiday settings 
        self.holiday_group = QGroupBox("holidays (max 3)")
        self.holiday_layout = QVBoxLayout()
        self.holiday_layout.setContentsMargins(6, 20, 6, 6)
        self.holiday_layout.addSpacing(6)
        self.holiday_group.setLayout(self.holiday_layout)
        self.main_layout.addWidget(self.holiday_group)

        # holiday list
        self.holiday_list_widget = QListWidget()
        self.holiday_list_widget.itemDoubleClicked.connect(self.edit_holiday)
        self.holiday_layout.addWidget(self.holiday_list_widget)

        # holiday buttons
        btn_layout = QHBoxLayout()
        self.add_holiday_btn = QPushButton("add holiday")
        self.remove_holiday_btn = QPushButton("remove selected")
        self.add_holiday_btn.clicked.connect(self.add_holiday)
        self.remove_holiday_btn.clicked.connect(self.remove_selected_holiday)
        btn_layout.addWidget(self.add_holiday_btn)
        btn_layout.addWidget(self.remove_holiday_btn)
        self.holiday_layout.addLayout(btn_layout)

        # state snapshot for dirty checking 
        self._snapshot = self._snapshot_state()
        self._temp_state = copy.deepcopy(self._snapshot)
        self.refresh_holiday_list()

        # save button 
        self.save_btn = QPushButton("save settings")
        self.save_btn.clicked.connect(self.save_settings)
        self.main_layout.addWidget(self.save_btn)
        self.save_btn.setEnabled(False)

        # header fonts
        self.header_font = QFont()
        self.header_font.setPointSize(16)
        for group in [self.general_group, self.meal_group, self.holiday_group]:
            group.setFont(self.header_font)

        # connect theme change
        self.theme_box.currentTextChanged.connect(self.on_theme_changed)
        self.util.apply_theme()

    # helpers
    def _set_timeedit_value(self, time_edit, new_time) -> None:
        """a helper to set QTimeEdit properly"""
        time_edit.blockSignals(True)
        time_edit.setTime(new_time)
        time_edit.blockSignals(False)

    def _snapshot_state(self) -> dict:
        """a helper to snapshot the current state"""
        return {
            "theme": self.theme_box.currentText(),
            "weekday_start": self.start_time_edit.time().toString("HH:mm"),
            "weekday_end": self.end_time_edit.time().toString("HH:mm"),
            "weekend_start": self.weekend_start_edit.time().toString("HH:mm"),
            "weekend_end": self.weekend_end_edit.time().toString("HH:mm"),
            "break_duration": self.break_duration_spin.value(),
            "break_interval": self.break_interval_spin.value(),
            "notification_frequency": self.notification_spin.value(),
            "meal_windows": {
                meal: (start.time().toString("HH:mm"), end.time().toString("HH:mm"))
                for meal, (start, end) in self.meal_edits.items()
            },
            "meal_duration": self.meal_duration_spin.value(),
            "holidays": list(self.settings.holiday_ranges)
        }

    def _is_dirty(self) -> bool:
        """a helper to check if the state is dirty"""
        return self._temp_state != self._snapshot

    def _update_save_state(self):
        self.save_btn.setEnabled(self._is_dirty())

    # save settings
    def save_settings(self, skip_confirmation=False):
        if not self._is_dirty():
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Save",
            "Do you want to save your settings?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        # save all settings
        self.settings.theme = self._temp_state["theme"]
        self.settings.start_time = QTime.fromString(self._temp_state["weekday_start"], "HH:mm").toPyTime()
        self.settings.end_time = QTime.fromString(self._temp_state["weekday_end"], "HH:mm").toPyTime()
        self.settings.weekend_start = QTime.fromString(self._temp_state["weekend_start"], "HH:mm").toPyTime()
        self.settings.weekend_end = QTime.fromString(self._temp_state["weekend_end"], "HH:mm").toPyTime()
        self.settings.break_duration = timedelta(minutes=self._temp_state["break_duration"])
        self.settings.break_interval = timedelta(minutes=self._temp_state["break_interval"])
        self.settings.notification_frequency = timedelta(minutes=self._temp_state["notification_frequency"])

        for meal, (s, e) in self._temp_state["meal_windows"].items():
            self.settings.meal_windows[meal] = (
                QTime.fromString(s, "HH:mm").toPyTime(),
                QTime.fromString(e, "HH:mm").toPyTime()
            )
        self.settings.meal_duration = timedelta(minutes=self._temp_state["meal_duration"])
        self.settings.holiday_ranges = list(self._temp_state["holidays"])
        self.persistence.save_settings(self.settings)

        self._snapshot = copy.deepcopy(self._temp_state)
        self._update_save_state()

    # break and notification changes
    def on_break_interval_changed(self, value):
        snapped = self.util.snap_to_5_minutes(value)
        self.break_interval_spin.blockSignals(True)
        self.break_interval_spin.setValue(snapped)
        self.break_interval_spin.blockSignals(False)
        self._temp_state["break_interval"] = snapped
        self._update_save_state()

    def on_break_duration_changed(self, value):
        snapped = self.util.snap_to_5_minutes(value)
        self.break_duration_spin.blockSignals(True)
        self.break_duration_spin.setValue(snapped)
        self.break_duration_spin.blockSignals(False)
        self._temp_state["break_duration"] = snapped
        self._update_save_state()

    def on_notification_duration_changed(self, value):
        snapped = self.util.snap_to_5_minutes(value)
        self.notification_spin.blockSignals(True)
        self.notification_spin.setValue(snapped)
        self.notification_spin.blockSignals(False)
        self._temp_state["notification_frequency"] = snapped
        self._update_save_state()

    # back button handling
    def on_back_clicked(self):
        if self._is_dirty():
            reply = QMessageBox.question(
                self,
                "unsaved changes",
                "you have unsaved changes. do you want to save before going back?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if reply == QMessageBox.Yes:
                self.save_settings(True)
                self.back.emit()
            elif reply == QMessageBox.No:
                self.back.emit()
            else:
                pass  # Cancel, stay
        else:
            self.back.emit()

    # holiday management
    def add_holiday(self):
        if len(self._temp_state["holidays"]) >= 3:
            QMessageBox.warning(self, "max holidays", "you can only have up to 3 holidays.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("add holiday")
        layout = QVBoxLayout(dialog)

        calendar_start = QCalendarWidget()
        calendar_end = QCalendarWidget()
        layout.addWidget(QLabel("start date"))
        layout.addWidget(calendar_start)
        layout.addWidget(QLabel("end date"))
        layout.addWidget(calendar_end)

        save_btn = QPushButton("add")
        save_btn.clicked.connect(lambda: self.save_holiday(dialog, calendar_start, calendar_end))
        layout.addWidget(save_btn)

        dialog.setLayout(layout)
        dialog.exec_()

    def save_holiday(self, dialog, start_cal, end_cal):
        start_date = start_cal.selectedDate().toPyDate()
        end_date = end_cal.selectedDate().toPyDate()

        if start_date > end_date:
            QMessageBox.warning(self, "invalid range", "start date cannot be after end date.")
            return

        if len(self._temp_state["holidays"]) >= 3:
            QMessageBox.warning(self, "max holidays", "you can only have up to 3 holidays.")
            return

        self._temp_state["holidays"].append((start_date, end_date))
        self.refresh_holiday_list()
        self._update_save_state()
        dialog.accept()

    def edit_holiday(self, item):
        index = self.holiday_list_widget.row(item)
        start, end = self._temp_state["holidays"][index]

        dialog = QDialog(self)
        dialog.setWindowTitle("edit holiday")
        layout = QVBoxLayout(dialog)

        calendar_start = QCalendarWidget()
        calendar_end = QCalendarWidget()
        calendar_start.setSelectedDate(QDate(start.year, start.month, start.day))
        calendar_end.setSelectedDate(QDate(end.year, end.month, end.day))

        layout.addWidget(QLabel("start date"))
        layout.addWidget(calendar_start)
        layout.addWidget(QLabel("end date"))
        layout.addWidget(calendar_end)

        save_btn = QPushButton("save")
        save_btn.clicked.connect(lambda: self.save_edited_holiday(dialog, index, calendar_start, calendar_end))
        layout.addWidget(save_btn)

        dialog.setLayout(layout)
        dialog.exec_()

    def save_edited_holiday(self, dialog, index, start_cal, end_cal):
        start_date = start_cal.selectedDate().toPyDate()
        end_date = end_cal.selectedDate().toPyDate()

        if start_date > end_date:
            QMessageBox.warning(self, "invalid range", "start date cannot be after end date.")
            return

        self._temp_state["holidays"][index] = (start_date, end_date)
        self.refresh_holiday_list()
        self._update_save_state()
        dialog.accept()

    def remove_selected_holiday(self):
        selected_items = self.holiday_list_widget.selectedItems()
        if not selected_items:
            return
        for item in selected_items:
            index = self.holiday_list_widget.row(item)
            del self._temp_state["holidays"][index]
        self.refresh_holiday_list()
        self._update_save_state()

    def refresh_holiday_list(self):
        """Refresh holiday list widget, sorted by start date."""
        self.holiday_list_widget.clear()
        sorted_holidays = sorted(self._temp_state["holidays"], key=lambda x: x[0])
        for start, end in sorted_holidays:
            start_qdate = QDate(start.year, start.month, start.day)
            end_qdate = QDate(end.year, end.month, end.day)
            start_day = start_qdate.toString("ddd")
            end_day = end_qdate.toString("ddd")
            item_text = f"{start_day} {start} → {end_day} {end}"
            item = QListWidgetItem(item_text)
            item.setToolTip("Double click to edit")
            self.holiday_list_widget.addItem(item)

    # weekday validation
    def validate_weekday_times(self):
        self._validate_day_times(self.start_time_edit, self.end_time_edit, "weekday_start", "weekday_end")
        self.enforce_breakfast_rule()

    # weekend validation 
    def validate_weekend_times(self):
        self._validate_day_times(self.weekend_start_edit, self.weekend_end_edit, "weekend_start", "weekend_end")
        self.enforce_breakfast_rule()

    def _validate_day_times(self, start_edit, end_edit, start_key, end_key):
        """Validate a day's start/end times and snap to 5-min increments."""
        start_time = start_edit.time()
        end_time = end_edit.time()

        # invalid range check (start >= end or duration > 10 hours)
        if start_time >= end_time or start_time.addSecs(10 * 60 * 60) > end_time:
            ts = self._temp_state[start_key]
            te = self._temp_state[end_key]
            self._set_timeedit_value(start_edit, QTime.fromString(ts, "HH:mm"))
            self._set_timeedit_value(end_edit, QTime.fromString(te, "HH:mm"))
            return

        today = QDate.currentDate()
        snapped_start = self.util.round_qdatetime_to_5(QDateTime(today, start_time)).time()
        snapped_end = self.util.round_qdatetime_to_5(QDateTime(today, end_time)).time()

        self._set_timeedit_value(start_edit, snapped_start)
        self._set_timeedit_value(end_edit, snapped_end)

        self._temp_state[start_key] = snapped_start.toString("HH:mm")
        self._temp_state[end_key] = snapped_end.toString("HH:mm")
        self._update_save_state()

    # breakfast enforcement
    def enforce_breakfast_rule(self):
        """Ensure breakfast ends at least 30 mins after latest day start."""
        b_start_edit, b_end_edit = self.meal_edits["breakfast"]
        latest_day_start = max(self.start_time_edit.time(), self.weekend_start_edit.time())
        min_end_time = latest_day_start.addSecs(30 * 60)

        if b_end_edit.time() < min_end_time:
            self._set_timeedit_value(b_end_edit, min_end_time)
            self._temp_state["meal_windows"]["breakfast"] = (
                b_start_edit.time().toString("HH:mm"),
                b_end_edit.time().toString("HH:mm")
            )
            self._update_save_state()

    # meal validation
    def validate_meal_times(self):
        """Ensure meals do not overlap and all times are snapped."""
        meals = sorted(
            [(meal, *edits) for meal, edits in self.meal_edits.items()],
            key=lambda x: x[1].time()
        )

        for i in range(len(meals) - 1):
            _, start_edit_i, end_edit_i = meals[i]
            _, start_edit_j, end_edit_j = meals[i + 1]

            if end_edit_i.time() > start_edit_j.time():
                # snap end of earlier meal to start of later meal
                self._set_timeedit_value(end_edit_i, start_edit_j.time())
                self._temp_state["meal_windows"][meals[i][0]] = (
                    start_edit_i.time().toString("HH:mm"),
                    end_edit_i.time().toString("HH:mm")
                )

        # snap all meals to nearest 5 mins
        today = QDate.currentDate()
        for meal, start_edit, end_edit in meals:
            snapped_start = self.util.round_qdatetime_to_5(QDateTime(today, start_edit.time())).time()
            snapped_end = self.util.round_qdatetime_to_5(QDateTime(today, end_edit.time())).time()
            self._set_timeedit_value(start_edit, snapped_start)
            self._set_timeedit_value(end_edit, snapped_end)
            self._temp_state["meal_windows"][meal] = (
                snapped_start.toString("HH:mm"),
                snapped_end.toString("HH:mm")
            )
        self._update_save_state()

    # meal duration change
    def on_meal_duration_changed(self, value):
        snapped = self.util.snap_to_5_minutes(value)
        self.meal_duration_spin.blockSignals(True)
        self.meal_duration_spin.setValue(snapped)
        self.meal_duration_spin.blockSignals(False)
        self._temp_state["meal_duration"] = snapped
        self._update_save_state()

    # theme change
    def on_theme_changed(self, text):
        self._temp_state["theme"] = text
        self.util.apply_theme(theme=self._temp_state["theme"])
        self._update_save_state()
