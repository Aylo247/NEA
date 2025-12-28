from datetime import datetime, timedelta
from blocks import task, eventblock

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
        tasks = []
        for i in self.blocks:
            if i.type == "task" and i.name not in {"breakfast", "lunch", "dinner", "break"}:
                tasks.append(i)

        return tasks

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
                block_dict["interval"] = block.interval if block.repeatable else 0

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
                block = eventblock(
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
        if block.start is not None and block.type == "task":
            self.global_edf_scheduler(ignore_blocks=[block])
        else:
            self.global_edf_scheduler()

    def clear_for_time(self, duration):
        now = datetime.now()
        if duration == "rest of day":
            tomorrow = now + timedelta(days=1)
            start_time, _ = self.settings.day_bounds(tomorrow)
        else:
            start_time = now + duration
            _, end_time = self.settings.day_bounds(now)
            if start_time > end_time:
                tomorrow = now + timedelta(days=1)
                start_time, _ = self.settings.day_bounds(tomorrow)
        self.global_edf_scheduler(start_time=start_time)


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

    def global_edf_scheduler(self, pointer = None, ignore_blocks = None):
        """
        Schedules a list of Block objects globally using EDF.
        Modifies task start times and adds missing special blocks (meals/breaks).
        
        Args:
            self
            pointer: an optional datetime to start scheduling from
            ignore_blocks: an optional list of blocks to ingnore during scheduling
        
        Returns:
            List of Block objects with updated start times.
        """
        SPECIAL_NAMES = {"breakfast", "lunch", "dinner", "break"}
        BREAK_INTERVAL = self.settings.break_interval
        BREAK_DURATION = self.settings.break_duration
        MEAL_DURATION = self.settings.meal_duration


        # Helper functions
        def find_next_available(start_time, duration, current_schedule):

            """
            Finds earliest start time >= start_time to fit a block of duration,
            avoiding all fixed events and already scheduled tasks/specials.
            """

            current = start_time
            while True:
                conflict = False
                day_start, day_end = self.settings.get_day_bounds(current)
                if current < day_start:
                    current = day_start
                if current + duration > day_end:
                    # Move to next day start
                    next_day = current + timedelta(days=1)
                    next_day_start, _ = self.settings.get_day_bounds(next_day)
                    current = datetime.combine(next_day.date(), next_day_start.time())
                    continue

                for b in current_schedule:
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

        def meal_valid(meal_name, scheduled_blocks, pointer):
            day_blocks = [b for b in scheduled_blocks if b.start is not None and b.start.date() == pointer.date()]
            meal_start, meal_end = self.settings.meal_windows[meal_name]
            meal_start = datetime.combine(pointer.date(), meal_start)
            meal_end = datetime.combine(pointer.date(), meal_end) - MEAL_DURATION
            if any(b.name == meal_name for b in day_blocks) or not(meal_start <= pointer <= meal_end):
                return False
            return True
        
        def break_valid(pointer, scheduled_blocks):
            """
            Determines if a break can be scheduled at 'pointer' on that day.
            
            Args:
                pointer: datetime to check for break placement
                scheduled_blocks: list of all scheduled blocks
                break_duration: timedelta of the break length
                break_interval: minimum timedelta since last break
                settings: schedule settings for day bounds
            
            Returns:
                True if a break can be scheduled at pointer, False otherwise
            """
            day_start, day_end = self.settings.get_day_bounds(pointer)
            if pointer + BREAK_DURATION > day_end:
                return False  # break won't fit before end of day

            # Get only blocks for the same day
            day_blocks = [b for b in scheduled_blocks if b.start.date() == pointer.date()]
            day_blocks.sort(key=lambda b: b.start)

            # Check backward: has enough time passed since last break (including meals)
            duration_since_last_break = timedelta(0)
            for b in reversed(day_blocks):
                if b.start >= pointer:
                    continue  # only consider blocks before pointer
                if b.name in {"break", "breakfast", "lunch", "dinner"}:
                    return False  # recent break or meal found
                duration_since_last_break += b.duration
                if duration_since_last_break >= BREAK_INTERVAL:
                    break

            # Check forward: ensure break won't overlap future blocks
            for b in day_blocks:
                if b.start >= pointer + BREAK_DURATION:
                    break  # no conflict with this or future blocks
                if pointer < b.start + b.duration and pointer + BREAK_DURATION > b.start:
                    return False  # overlap detected

            return True



        # Deep copy if needed to avoid mutating original list
        scheduled_blocks = self.blocks[:]

        # Separate tasks, events, and special blocks
        ignore_blocks = ignore_blocks if ignore_blocks else []
        tasks = [
            b for b in scheduled_blocks
            if b.type == 'task' and not b.is_completed and not b.name in SPECIAL_NAMES and b not in ignore_blocks
        ]
        completed_tasks = [
            b for b in scheduled_blocks
            if b.type == 'task' and b.is_completed and not b.name in SPECIAL_NAMES and b not in ignore_blocks
        ]
        events = [b for b in scheduled_blocks if isinstance(b, eventblock)]
        current_schedule = [
            e for e in events
            if not (e.repeatable and self.settings.is_holiday(e.start))
        ]
        for b in current_schedule:
            if getattr(b, "repeatable", True):
                repeat_interval = timedelta(days=b.interval)
                next_start = b.start + repeat_interval
                while next_start <= datetime.now() + timedelta(days=42):
                    if not self.settings.is_holiday(next_start):
                        # Check if an event with the same name and start already exists
                        exists = any(
                            existing.name == b.name and existing.start == next_start
                            for existing in current_schedule
                        )
                        if not exists:
                            repeated_event = eventblock(
                                name=b.name,
                                start=next_start,
                                duration=b.duration,
                                location=getattr(b, "location", None),
                                notes=getattr(b, "notes", None),
                                is_fixed=b.is_fixed,
                                priority=b.priority,
                                repeatable=b.repeatable,
                                interval=b.interval
                            )
                            current_schedule.append(repeated_event)
                    next_start += repeat_interval

        current_schedule = current_schedule + ignore_blocks
        current_schedule.sort(key=lambda b: b.start)

        # Sort tasks by earliest deadline (EDF)
        tasks.sort(key=lambda t: t.deadline)
        # Schedule tasks
        meal_names = ["breakfast", "lunch", "dinner"]
        pointer = pointer if pointer else datetime.combine(self.date, self.settings.start_time)
        for t in tasks:
            t.start = find_next_available(pointer, t.duration, current_schedule)
            pointer = t.start + t.duration
            current_schedule.append(t)
            meal_placed = False
            for i in meal_names:
                possible_start = find_next_available(pointer, MEAL_DURATION, current_schedule)
                if meal_valid(i, current_schedule, possible_start):
                    meal = task(
                        name = i,
                        start = possible_start,
                        duration = MEAL_DURATION,
                    )
                    current_schedule.append(meal)
                    pointer = possible_start + MEAL_DURATION
                    meal_placed = True
                    break

            if not meal_placed:       
                
                possible_start = find_next_available(pointer, BREAK_DURATION, current_schedule)
                if break_valid(possible_start, current_schedule):
                    break_block = task(
                        name = "break",
                        start = possible_start,
                        duration = BREAK_DURATION,
                    )
                    current_schedule.append(break_block)
                    pointer = possible_start + BREAK_DURATION 
            
        all_dates = set()
        for b in current_schedule:
            # Use the block's start if it exists, otherwise use its deadline date
            if b.start is not None:
                all_dates.add(b.start.date())
            elif hasattr(b, 'deadline') and b.deadline is not None:
                all_dates.add(b.deadline.date())
        for date in all_dates:
            ensure_meals_for_date(date, current_schedule)

        self.blocks = current_schedule + completed_tasks


