import json
from datetime import date, time, datetime, timedelta

class Block(): 
    def __init__(self, name, start, end, location = None, notes = None , is_fixed = False):
        self.name = name 
        self.start = start
        self.end = end
        self.location = location
        self.notes = notes
        self.is_fixed = is_fixed

    @property
    def duration(self):
        return self.end - self.start
    
    def edit(self,**kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def move(self, new_start, new_end):
        if self.is_fixed:
            raise ValueError("Cannot move a fixed block.")
        self.start = new_start
        self.end = new_end


class event(Block):
    def __init__(self, name, start, end, location = "", notes = "" , is_fixed = True, priority = 0, repeatable = False, interval = None):
        super().__init__(name, start, end, location, notes, is_fixed)
        self.priority = priority
        self.repeatable = repeatable
        self.type = "event"
        self.repeatinterval = interval

class task(Block):
    def __init__(self, name, start, end, deadline = None, location = "", notes = "" , is_fixed = False):
        super().__init__(name, start, end, location, notes, is_fixed)
        self.deadline = deadline
        self.is_completed = False
        self.completed_at = None
        self.type = "task"

    def mark_complete(self):
        if self.is_completed:
            return
        self.is_completed = True
        self.completed_at = datetime.now()

    def mark_incomplete(self):
        if not self.is_completed:
            return
        self.is_completed = False
        self.completed_at = None

    def auto_reschedule(self, new_start):
        if self.is_completed:
            return
        self.start = new_start
        self.end = new_start + self.duration

class Schedule:
    def __init__(self):
        self.date = datetime.now().date()
        self.blocks = []

    def to_dict(self):
        schedule_dict = {"name": "Schedule", "blocks": []}

        for block in self.blocks:
            block_dict = {
                "type": block.type,
                "name": block.name,
                "start": block.start.isoformat(),
                "end": block.end.isoformat(),
                "location": block.location or "",
                "notes": block.notes or "",
                "is_fixed": block.is_fixed
            }

            if block.type == "event":
                block_dict["priority"] = block.priority
                block_dict["repeatable"] = block.repeatable
                block_dict["interval"] = block.repeatinterval if block.repeatable else None

            elif block.type == "task":
                block_dict["deadline"] = block.deadline.isoformat() if block.deadline else None
                block_dict["is_completed"] = block.is_completed
                block_dict["completed_at"] = block.completed_at.isoformat() if block.completed_at else None

            # Add block dict to schedule
            schedule_dict["blocks"].append(block_dict)

        return schedule_dict
    
    def from_dict(self, data):
        self.blocks = []
        for block_data in data.get("blocks", []):
            if block_data["type"] == "event":
                block = event(
                    name=block_data["name"],
                    start=datetime.fromisoformat(block_data["start"]),
                    end=datetime.fromisoformat(block_data["end"]),
                    location=block_data.get("location"),
                    notes=block_data.get("notes"),
                    is_fixed=block_data.get("is_fixed", False),
                    priority=block_data.get("priority", 0),
                    repeatable=block_data.get("repeatable", False),
                    interval=block_data.get("interval")

                )
            else:
                block = task(
                    name=block_data["name"],
                    start=datetime.fromisoformat(block_data["start"]),
                    end=datetime.fromisoformat(block_data["end"]),
                    deadline=datetime.fromisoformat(block_data["deadline"]) if block_data.get("deadline") else None,
                    location=block_data.get("location"),
                    notes=block_data.get("notes"),
                    is_fixed=block_data.get("is_fixed", False)
                )
                block.is_completed = block_data.get("is_completed", False)
                if block.is_completed:
                    block.completed_at = datetime.fromisoformat(block_data["completed_at"])
                else: 
                    None
            self.blocks.append(block)

    def day(self, date):
        day_blocks = []
        for block in self.blocks:
            if block.start.date() == date:
                day_blocks.append(block)
        return day_blocks

    def week(self, week_start_date):
        week_blocks = []
        for block in self.blocks:
            if block.start.date() >= week_start_date and block.start.date() < week_start_date + timedelta(days=7):
                week_blocks.append(block)
        return week_blocks
    
    def month(self, month_start_date):
        while month_start_date.strftime("%A") != "Monday":
            month_start_date -= timedelta(days=1)

        month_blocks = []
        for block in self.blocks:
            if block.start.date() >= month_start_date and block.start.date() < month_start_date + timedelta(days=35):
                month_blocks.append(block)
        return month_blocks
    

    def add_block(self, block):
        self.blocks.append(block)

    def remove_block(self, block):
        if block in self.blocks:
            self.blocks.remove(block)

    def find_conflicts(self):
        pass

    def auto_arrange(self):
        pass

    def clear_time_range(self, start, end):
        pass

class ToDoList:

    def __init__(self):
        self.tasks = [] # list of TaskBlock instances

    def take_tasks_from_schedule(self, schedule):
        for block in schedule.blocks:
            if isinstance(block, task):
                self.tasks.append(block)
                schedule.remove_block(block)

    def add_task(self, task):
        self.tasks.append(task)

    def remove_task(self, task):
        if task in self.tasks:
            self.tasks.remove(task)

    def mark_complete(self, task):
        if task in self.tasks:
            task.mark_complete()

    def mark_incomplete(self, task):
        if task in self.tasks:
            task.mark_incomplete()

    def clean_old_tasks(self, older_than):
        now = datetime.now()
        self.tasks = [
            task for task in self.tasks
            if not task.is_completed or (task.completed_at and now - task.completed_at <= older_than)
        ]

class Settings:
    def __init__(self):
        self.theme = "Light"
        self.start_time = time(7, 0)
        self.end_time = time(22, 0)
        self.notification_frequency = timedelta(minutes=30)
        self.meal_windows = {"Breakfast": (time(7,0), time(9,0)),
                             "Lunch": (time(12,0), time(14,0)),
                             "Dinner": (time(18,0), time(20,0))}
        self.break_durations = {"short": timedelta(minutes=10),
                                "long": timedelta(minutes=30)}
        self.history_duration = timedelta(days=7)
        self.holiday_ranges = []  # list of tuples (start_date, end_date)

    def to_dict(self):
        settings_dict = {
            "theme": self.theme,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "notification_frequency": self.notification_frequency.total_seconds(),
            "meal_windows": {
                meal: (start.isoformat(), end.isoformat())
                for meal, (start, end) in self.meal_windows.items()
            },
            "break_durations": {
                name: duration.total_seconds()
                for name, duration in self.break_durations.items()
            },
            "history_duration": self.history_duration.total_seconds(),
            "holiday_ranges": [
                (start.isoformat(), end.isoformat())
                for start, end in self.holiday_ranges
            ]
        }
        return settings_dict
    
    def from_dict(self, data):
        self.theme = data.get("theme", self.theme)
        self.start_time = time.fromisoformat(data.get("start_time", self.start_time.isoformat()))
        self.end_time = time.fromisoformat(data.get("end_time", self.end_time.isoformat()))
        self.notification_frequency = timedelta(seconds=data.get("notification_frequency", self.notification_frequency.total_seconds()))
        
        meal_windows_data = data.get("meal_windows", {})
        self.meal_windows = {
            meal: (time.fromisoformat(start), time.fromisoformat(end))
            for meal, (start, end) in meal_windows_data.items()
        }
        
        break_durations_data = data.get("break_durations", {})
        self.break_durations = {
            name: timedelta(seconds=duration)
            for name, duration in break_durations_data.items()
        }
        
        self.history_duration = timedelta(seconds=data.get("history_duration", self.history_duration.total_seconds()))
        
        holiday_ranges_data = data.get("holiday_ranges", [])
        self.holiday_ranges = [
            (date.fromisoformat(start), date.fromisoformat(end))
            for start, end in holiday_ranges_data
        ]

    def update(self, PersistenceManager, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        PersistenceManager.save_settings(self)

    def add_holiday(self, start_date, end_date):
        self.holiday_ranges.append((start_date, end_date))

    def clean_past_holidays(self):
        today = date.today()
        self.holiday_ranges = [
            (start, end) for start, end in self.holiday_ranges
            if end >= today
        ]

class PersistenceManager:

    def __init__(self):
        self.data_file = "data.json"
        self.settings_file = "settings.json"

    def save_settings(self, settings):
        if settings is None:
            return None
        data_to_save = {}
        if settings is not None:
            data_to_save['settings'] = settings.to_dict()
        
        json_data = json.dumps(data_to_save, indent=4)
        with open(self.settings_file, 'w') as f:
            f.write(json_data)

    def load_settings(self):
        try:
            with open(self.settings_file, 'r') as f:
                json_data = f.read()
                data = json.loads(json_data)
                return data.get('settings', {})
        except FileNotFoundError:
            return {}

    def save_data(self, schedule=None):
        if schedule is None:
            return None
        data_to_save = {}
        if schedule is not None:
            data_to_save['schedule'] = schedule.to_dict()
        
        json_data = json.dumps(data_to_save, indent=4)
        with open(self.data_file, 'w') as f:
            f.write(json_data)

    def load_data(self):
        try:
            with open(self.data_file, 'r') as f:
                json_data = f.read()
                data = json.loads(json_data)
                return data
        except FileNotFoundError:
            return {}

    def save_all(self, schedule, settings):
        self.save_data(schedule)
        self.save_settings(settings)