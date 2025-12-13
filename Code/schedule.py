from datetime import datetime, timedelta
from blocks import task, event

"""
The Schedule class manages a collection of time blocks, including events and tasks.
It provides methods to add, remove, and retrieve blocks for specific time periods,
as well as functionality to serialize and deserialize the schedule data.
"""

class Schedule:
    def __init__(self):
        self.date = datetime.now().date()
        self.blocks = []

    @property
    def ToDoList(self):
        self.tasks = []
        for block in self.blocks:
            if isinstance(block, task):
                self.tasks.append(block)
        return self.tasks

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
    
    #adds\removes blocks and mark tasks as complete\incomplete
    def add_block(self, block):
        self.blocks.append(block)

    def remove_block(self, block):
        if block in self.blocks:
            self.blocks.remove(block)

    def mark_complete(self, task):
        if task in self.blocks:
            task.mark_complete()

    def mark_incomplete(self, task):
        if task in self.blocks:
            task.mark_incomplete()



    def find_conflicts(self):
        pass

    def auto_arrange(self):
        pass

    def clear_time_range(self, start, duration):
        pass


    #cleans old completed tasks and events based on a specified duration that will be spcified in setings
    def clean_old_blocks(self, older_than):
        now = datetime.now()
        for i in self.blocks:
            if i.type == "task" and i.is_completed and i.completed_at is not None:
                if now - i.completed_at > older_than:
                    self.blocks.remove(i)
            elif i.type == "event":
                if now - i.end > older_than:
                    self.blocks.remove(i)
 