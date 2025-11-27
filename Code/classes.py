import json
from datetime import date, time, datetime, timedelta

def Block(): 
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
    
    def edit(self):
        pass

    def delete(self):
        pass

    def move(self, new_start, new_end):
        if self.is_fixed:
            raise ValueError("Cannot move a fixed block.")
        self.start = new_start
        self.end = new_end


def event(Block):
    def __init__(self, name, start, end, priority = 0, location = "", notes = "" , is_fixed = True):
        super().__init__(name, start, end, location, notes, is_fixed)
        self.priority = priority

def task(Block):
    def __init__(self, name, start, end, deadline = None, location = "", notes = "" , is_fixed = False):
        super().__init__(name, start, end, location, notes, is_fixed)
        self.deadline = deadline
        self.is_completed = False
        self.completed_at = None

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

    def day(self, date):
        pass

    def week(self, week_start_date):
        pass

    def add_block(self, block):
        pass

    def remove_block(self, block):
        pass

    def find_conflicts(self):
        pass

    def auto_arrange(self):
        pass

    def clear_time_range(self, start, end):
        pass

class ToDoList:

    def __init__(self):
        self.tasks = [] # list of TaskBlock instances

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

    def update(self):
        pass

    def add_holiday(self, start_date, end_date):
        self.holiday_ranges.append((start_date, end_date))

    def clean_past_holidays(self):
        today = date.today()
        self.holiday_ranges = [
            (start, end) for start, end in self.holiday_ranges
            if end >= today
        ]

class PersistenceManager:

    def __init__(self, data_file, settings_file):
        self.data_file = data_file
        self.settings_file = settings_file

    def _serialize(self, obj):
        if isinstance(obj, (datetime, date, time)):
            return obj.isoformat()
        elif isinstance(obj, timedelta):
            return obj.total_seconds()
        elif isinstance(obj, list):
            return [self._serialize(i) for i in obj]
        elif isinstance(obj, dict):
            return {k: self._serialize(v) for k, v in obj.items()}
        else:
            return obj

    def save_settings(self, settings):
        pass

    def load_settings(self):
        pass

    def save_data(self, schedule=None, todo_list=None):
        pass

    def load_data(self):
        pass

    def save_all(self, schedule, todo_list, settings):
        data_to_save = {
        'schedule_blocks': schedule.blocks,
        'todo_tasks': todo_list.tasks,
    }
        self.save_data(data_to_save)
        self.save_settings(settings)