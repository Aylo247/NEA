from datetime import datetime, timedelta
from blocks import task, event

"""
The Schedule class manages a collection of time blocks, including events and tasks.
It provides methods to add, remove, and retrieve blocks for specific time periods,
as well as functionality to serialize and deserialize the schedule data.
"""

class Schedule:
    def __init__(self, settings):
        self.date = datetime.now().date()
        self.blocks = []
        self.settings = settings

    @property
    def ToDoList(self):
        return [b for b in self.blocks if isinstance(b, task)]

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
        self.global_edf_scheduler()

    def remove_block(self, block):
        if block in self.blocks:
            self.blocks.remove(block)
        self.global_edf_scheduler()

    def mark_complete(self, task):
        if task in self.blocks:
            task.mark_complete()
        self.global_edf_scheduler()

    def mark_incomplete(self, task):
        if task in self.blocks:
            task.mark_incomplete()
        self.global_edf_scheduler()

    def global_edf_scheduler(self, pointer = None, ignore_blocks = None, start_time = None):
        """
        Schedules a list of Block objects globally using EDF.
        Modifies task start times and adds missing special blocks (meals/breaks).
        
        Args:
            self
        
        Returns:
            List of Block objects with updated start times.
        """
        SPECIAL_NAMES = {"breakfast", "lunch", "dinner", "break"}
        BREAK_INTERVAL = timedelta(hours=1, minutes=30)
        BREAK_DURATION = self.settings.break_duration
        MEAL_DURATION = timedelta(minutes=30)


        # Helper functions
        def is_holiday(check_date):
            for start, end in self.settings.holiday_ranges:
                if start <= check_date.date() <= end:
                    return True
            return False

        def get_day_bounds(dt):
            # weekday: 0=Mon, 6=Sun
            weekday = dt.weekday()
            if is_holiday(dt) or weekday >= 5:
                start = datetime.combine(dt.date(), self.settings.weekend_start)
                end = datetime.combine(dt.date(), self.settings.weekend_end)
            else:
                start = datetime.combine(dt.date(), self.settings.start_time)
                end = datetime.combine(dt.date(), self.settings.end_time)
            return start, end

        def find_next_available(start_time, duration, current_schedule, ignore_blocks=None):

            """
            Finds earliest start time >= start_time to fit a block of duration,
            avoiding all fixed events and already scheduled tasks/specials.
            """
            if ignore_blocks is None:
                ignore_blocks = []

            current = start_time
            while True:
                conflict = False
                day_start, day_end = get_day_bounds(current)
                if current < day_start:
                    current = day_start
                if current + duration > day_end:
                    # Move to next day start
                    next_day = current + timedelta(days=1)
                    next_day_start, _ = get_day_bounds(next_day)
                    current = datetime.combine(next_day.date(), next_day_start.time())
                    continue

                for b in current_schedule:
                    if b in ignore_blocks:
                        continue
                    b_start = b.start
                    b_end = b.start + b.duration
                    # Check overlap
                    if current < b_end and current + duration > b_start:
                        conflict = True
                        current = b_end
                        break

                if not conflict:
                    return current

        def ensure_meals_for_date(date, current_schedule):
            """Ensure breakfast, lunch, dinner exist for the given date."""

            for meal_name in ["breakfast", "lunch", "dinner"]:
                # Check if the meal already exists
                exists = any(
                    b.name.lower() == meal_name and b.start.date() == date
                    for b in current_schedule
                )
                if exists:
                    continue

                # Filter blocks on that day that might conflict
                day_blocks = sorted(
                    [b for b in current_schedule if b.start is not None and b.start.date() == date],
                    key=lambda b: b.start
                )

                # Meal window for that meal
                meal_start_time, meal_end_time = self.settings.meal_windows[meal_name]
                pointer = datetime.combine(date, meal_start_time)
                meal_window_end = datetime.combine(date, meal_end_time) - MEAL_DURATION

                # Try to fit the meal in the window
                while pointer <= meal_window_end:
                    conflict = False
                    for b in day_blocks:
                        b_start = b.start
                        b_end = b.start + b.duration
                        # If the meal overlaps this block, move pointer to end of block
                        if pointer < b_end and pointer + MEAL_DURATION > b_start:
                            pointer = b_end
                            conflict = True
                            break
                    if not conflict:
                        # Place the meal
                        meal_block = task(
                            name=meal_name,
                            start=pointer,
                            duration=MEAL_DURATION,
                        )
                        current_schedule.append(meal_block)
                        break  # meal scheduled
                    # Otherwise loop continues with updated pointer


        def meal_valid(meal_name, scheduled_blocks, pointer, date):
            day_blocks = [b for b in scheduled_blocks if b.start is not None and b.start.date() == date]
            meal_start, meal_end = self.settings.meal_windows[meal_name]
            meal_start = datetime.combine(date, meal_start)
            meal_end = datetime.combine(date, meal_end) - MEAL_DURATION
            if any(b.name == meal_name for b in day_blocks) or not(meal_start <= pointer <= meal_end):
                return False
            return True
        
        def break_valid(scheduled_blocks):
            duration_since_last_break = timedelta(0)
            last_block_index = -1
            try:
                while duration_since_last_break < BREAK_INTERVAL:
                    last_block = scheduled_blocks[last_block_index]
                    if last_block.name == "break":
                        return False
                    duration_since_last_break += last_block.duration
                    last_block_index -= 1
                return True
            except IndexError:
                return True

        # Deep copy if needed to avoid mutating original list
        scheduled_blocks = self.blocks[:]

        # Separate tasks, events, and special blocks
        ignore_blocks = ignore_blocks if ignore_blocks else []
        tasks = [
            b for b in scheduled_blocks
            if isinstance(b, task) and not b.is_completed and not b.name in SPECIAL_NAMES
        ]
        events = [b for b in scheduled_blocks if isinstance(b, event)]
        current_schedule = [
            e for e in events
            if not (e.repeatable and is_holiday(e.start))
        ]

        current_schedule = current_schedule + ignore_blocks
        current_schedule.sort(key=lambda b: b.start)

        # all_dates = set()
        # for b in tasks + events:
        #     # Use the block's start if it exists, otherwise use its deadline date
        #     if b.start is not None:
        #         all_dates.add(b.start.date())
        #     elif hasattr(b, 'deadline') and b.deadline is not None:
        #         all_dates.add(b.deadline.date())
        # Sort tasks by earliest deadline (EDF)
        tasks.sort(key=lambda t: t.deadline)
        # Schedule tasks
        meal_names = ["breakfast", "lunch", "dinner"]
        pointer = pointer if pointer else datetime.combine(self.date, self.settings.start_time)
        for t in tasks:
            t.start = find_next_available(pointer, t.duration, current_schedule)
            pointer = t.start + t.duration
            current_schedule.append(t)
            for i in meal_names:
                if meal_valid(i, current_schedule, t.start, t.start.date()):
                    meal = task(
                        name = i,
                        start = pointer,
                        duration = MEAL_DURATION,
                    )
                    current_schedule.append(meal)
                    pointer = pointer + MEAL_DURATION
                    continue
            if break_valid(current_schedule):
                break_block = task(
                    name = "break",
                    start = pointer,
                    duration = BREAK_DURATION,
                )
                current_schedule.append(break_block)
                pointer = pointer + BREAK_DURATION 
            
        all_dates = set()
        for b in current_schedule:
            # Use the block's start if it exists, otherwise use its deadline date
            if b.start is not None:
                all_dates.add(b.start.date())
            elif hasattr(b, 'deadline') and b.deadline is not None:
                all_dates.add(b.deadline.date())
        for date in all_dates:
            ensure_meals_for_date(date, current_schedule)

        # Optional: remove breaks if impossible to fit all tasks
        # (Skipping implementation for simplicity, could be added later)

        self.blocks = current_schedule