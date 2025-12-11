import json
from datetime import date, time, datetime, timedelta

#the base block class that other block types inherit from
class Block(): 
    def __init__(self, name, start, duration, location = None, notes = None , is_fixed = False):
        self.name = name  #e.g., "Doctor Appointment", "Study Session"
        self.start = start #datetime object
        self.duration = duration #timedelta object
        self.location = location #e.g., "Room 101", "Downtown Clinic"
        self.notes = notes #additional details
        self.is_fixed = is_fixed #True if the block cannot be moved or resized

    @property
    def end(self):
        return self.duration + self.start #datetime object
    
    def edit(self,**kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key): # check if attribute exists
                setattr(self, key, value)

    def move(self, new_start):
        if self.is_fixed:
            raise ValueError("Cannot move a fixed block.") #error should display a pop-up in the GUI
        self.start = new_start

#the event block that is fixed and cannot be moved
class event(Block):

    def __init__(self, name, start, duration, location = "", notes = "" , is_fixed = True, priority = 0, repeatable = False, interval = 0):
        super().__init__(name, start, duration, location, notes, is_fixed)
        self.priority = priority #0 for lowest an 2 for highest, for exambple a doctor appointment would be 2 but a lesson would be 1
        self.repeatable = repeatable
        self.type = "event"
        self.repeatinterval = interval

#the task block that is movable and can be marked complete or incomplete
class task(Block):
    def __init__(self, name, start, duration, deadline = None, location = "", notes = "" , is_fixed = False):
        super().__init__(name, start, duration, location, notes, is_fixed)
        self.deadline = deadline
        self.is_completed = False
        self.completed_at = None
        self.type = "task"

    def mark_complete(self):
        if self.is_completed:
            return
        self.is_completed = True
        self.completed_at = datetime.now() #for historical purposes

    def mark_incomplete(self):
        if not self.is_completed:
            return
        self.is_completed = False
        self.completed_at = None

#a class to manage custom block templates, allowing users to create, save, load, and instantiate templates
class CustomBlock():
    def __init__(self, templates = None):
        self.templates = templates if templates is not None else []

    #adds\removes custom block templates from only the in-memory list, not the actual file, that only happens when save() is called
    def add_template(self, template):
        self.templates.append(template)

    def delete_template(self, name):
        self.templates = [t for t in self.templates if t["name"] != name]

    #instantiates a block from a template with optional overrides
    def instantiate(self, template_name, **kwargs):
        template = next((t for t in self.templates if t["name"] == template_name), None)
        if not template:
            raise ValueError("Template not found")

        params = template.copy()
        params.update(kwargs)
        
        if params.get("type") == "event":
            name = params.get("name") 
            start = datetime.fromisoformat(params.get("start"))
            duration = timedelta(minutes=params.get("duration"))

            location = params.get("location", "")
            notes = params.get("notes", "")
            is_fixed = bool(params.get("is_fixed", True))
            priority = int(params.get("priority", 0))
            repeatable = bool(params.get("repeatable", False))
            interval = int(params.get("interval") if repeatable else 0)
            return event(name, start, duration, location, notes, is_fixed, priority, repeatable, interval)
        
        elif params.get("type") == "task":
            name = params.get("name")
            start = datetime.fromisoformat(params.get("start"))
            duration = timedelta(minutes=params.get("duration"))
            deadline = params.get("deadline", None)
            location = params.get("location", "")
            notes = params.get("notes", "")
            is_fixed = bool(params.get("is_fixed", False))
            return task(name, start, duration, deadline, location, notes, is_fixed)
        
        else:
            raise ValueError("Unknown block type")
    

#the main schedule class that holds all blocks and manages them
class Schedule:
    def __init__(self):
        self.date = datetime.now().date()
        self.blocks = []

    #converts the schedule and its blocks to and from a dictionary for easy JSON serialization by the PersistenceManager class
    def to_dict(self):
        schedule_dict = {"name": "Schedule", "blocks": []}

        for block in self.blocks:
            block_dict = {
                "type": block.type,
                "name": block.name,
                "start": block.start.isoformat(),
                "duration": block.duration.total_seconds() // 60,  # store duration in minutes
                "location": block.location or "",
                "notes": block.notes or "",
                "is_fixed": block.is_fixed
            }

            if block.type == "event":
                block_dict["priority"] = block.priority
                block_dict["repeatable"] = block.repeatable
                block_dict["interval"] = block.repeatinterval if block.repeatable else 0

            elif block.type == "task":
                block_dict["deadline"] = block.deadline.isoformat() if block.deadline else None
                block_dict["is_completed"] = block.is_completed
                block_dict["completed_at"] = block.completed_at.isoformat() if block.completed_at else None

            # Add block dict to schedule
            schedule_dict["blocks"].append(block_dict)

        return schedule_dict
    
    #same as above but reverses the process
    def from_dict(self, data):
        self.blocks = []
        for block_data in data.get("blocks", []):
            if block_data["type"] == "event":
                block = event(
                    name = block_data["name"],
                    start = datetime.fromisoformat(block_data["start"]),
                    duration = timedelta(minutes=block_data["duration"]),
                    location = block_data.get("location"),
                    notes = block_data.get("notes"),
                    is_fixed = bool(block_data.get("is_fixed", False)),
                    priority = int(block_data.get("priority", 0)),
                    repeatable = bool(block_data.get("repeatable", False)),
                    interval = int(block_data.get("interval", 0))

                )
            else:
                block = task(
                    name = block_data["name"],
                    start = datetime.fromisoformat(block_data["start"]),
                    duration = timedelta(minutes=block_data["duration"]),
                    deadline = datetime.fromisoformat(block_data["deadline"]) if block_data.get("deadline") else None,
                    location = block_data.get("location"),
                    notes = block_data.get("notes"),
                    is_fixed = bool(block_data.get("is_fixed", False))
                )
                block.is_completed = block_data.get("is_completed", False)
                if block.is_completed:
                    block.completed_at = datetime.fromisoformat(block_data["completed_at"])
                else: 
                    None
            self.blocks.append(block)

    
    #gets all blocks for a specific day, week or month
    def day(self, date):
        day_blocks = []
        for block in self.blocks:
            if block.start.date() == date:
                day_blocks.append(block)
        return day_blocks

    def week(self, week_start_date):
        while week_start_date.strftime("%A") != "Monday":
            week_start_date -= timedelta(days=1)

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
    
    #adds\removes blocks
    def add_block(self, block):
        self.blocks.append(block)

    def remove_block(self, block):
        if block in self.blocks:
            self.blocks.remove(block)

    def find_conflicts(self):
        pass

    def auto_arrange(self):
        pass

    def clear_time_range(self, start, duration):
        pass


#the to-do list class that manages tasks separately from the main schedule
class ToDoList:

    def __init__(self):
        self.tasks = [] 

    #takes tasks from the main schedule and adds them to the to-do list
    def take_tasks_from_schedule(self, schedule):
        for block in schedule.blocks:
            if isinstance(block, task):
                self.tasks.append(block)
                schedule.remove_block(block)

    #adds\removes tasks and marks them complete\incomplete
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

    #cleans old completed tasks based on a specified duration that will be spcified in setings
    def clean_old_tasks(self, older_than):
        now = datetime.now()
        self.tasks = [
            task for task in self.tasks
            if not task.is_completed or (task.completed_at and now - task.completed_at <= older_than)
        ]

#the settings class that holds all user preferences and configurations
class Settings:
    #initializes default settings
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

    #converts the settings to and from a dictionary for easy JSON serialization by the PersistenceManager class
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
                name: duration.total_seconds() // 60  # in minutes
                for name, duration in self.break_durations.items()
            },
            "history_duration": self.history_duration.total_seconds() // 86400,  # in days
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
            name: timedelta(minutes=duration)
            for name, duration in break_durations_data.items()
        }

        self.history_duration = timedelta(days=data.get("history_duration", self.history_duration.total_seconds() // 86400))
        holiday_ranges_data = data.get("holiday_ranges", [])
        self.holiday_ranges = [
            (date.fromisoformat(start), date.fromisoformat(end))
            for start, end in holiday_ranges_data
        ]

    #updates settings and saves them using the PersistenceManager
    def update(self, PersistenceManager, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        PersistenceManager.save_settings(self)

    #manages holiday ranges
    def add_holiday(self, start_date, end_date):
        self.holiday_ranges.append((start_date, end_date))

    def clean_past_holidays(self):
        today = date.today()
        self.holiday_ranges = [
            (start, end) for start, end in self.holiday_ranges
            if end >= today
        ]

#the persistence manager that handles saving and loading data and settings to and from JSON files
class PersistenceManager:
    def __init__(self):
        self.data_file = "data.json"
        self.settings_file = "settings.json"
        self.custom_blocks_file = "custom_blocks.json"

    #saves and loads custom block templates
    def load_custom_blocks(self):
        try:
            with open(self.custom_blocks_file, "r") as f:
                json_data = f.read()
                data = json.loads(json_data)
                return data.get('Templates', [])
        except FileNotFoundError:
            return []

    def save_custom_blocks(self, custom_blocks):
        if custom_blocks is None:
            return None
        data_to_save = {}
        if custom_blocks is not None:
            data_to_save['Templates'] = custom_blocks

        json_data = json.dumps(data_to_save, indent=4)
        with open(self.custom_blocks_file, 'w') as f:
            f.write(json_data)
        


    #saves and loads settings
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


    #saves and loads schedule data
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


    #a convenience method to save both schedule and settings at once
    def save_all(self, schedule, settings, custom_blocks):

        self.save_custom_blocks(custom_blocks)
        self.save_data(schedule)
        self.save_settings(settings)