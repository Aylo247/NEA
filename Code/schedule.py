from datetime import datetime, timedelta, date
from typing import List, Optional, Union
from blocks import Task, EventBlock
from PyQt5.QtGui import QColor

class Schedule:
    """
    manages a collection of time blocks (Tasks/EventBlocks), providing methods to
    add, remove, retrieve blocks for specific periods, and serialize/deserialize
    schedule data
    """

    def __init__(self, settings):
        self.date = datetime.now().date()
        self.blocks = []
        self.settings = settings

    @property
    def ToDoList(self) -> List:
        """return all tasks that are not meals/breaks"""
        return [b for b in self.blocks if b.type == "task" and b.name.lower() not in {"breakfast", "lunch", "dinner", "break"}]
    
    # serialization
    def to_dict(self) -> dict:
        """convert schedule and blocks to dictionary for JSON serialization"""
        schedule_dict = {"name": "Schedule", "blocks": []}
        for b in self.blocks:
            block_dict = {
                "type": b.type,
                "name": b.name,
                "start": b.start.isoformat(),
                "duration": b.duration.total_seconds() // 60,  # store in minutes
                "location": b.location,
                "notes": b.notes,
                "is_fixed": b.is_fixed,
                "colour": b.colour.name() if b.colour else None

            }
            if b.type == "event":
                block_dict.update({
                    "priority": b.priority,
                    "repeatable": b.repeatable,
                    "interval": b.interval if b.repeatable else 0
                })
            elif b.type == "task":
                block_dict.update({
                    "deadline": b.deadline.isoformat() if b.deadline else None,
                    "is_completed": b.is_completed,
                    "completed_at": b.completed_at.isoformat() if b.completed_at else None
                })
            schedule_dict["blocks"].append(block_dict)
        return schedule_dict

    def from_dict(self, data: dict) -> None:
        """load blocks from dictionary (inverse of to_dict)"""
        self.blocks = []
        for bd in data.get("blocks", []):
            colour = QColor(bd["colour"]) if bd.get("colour") else None
            if bd["type"] == "event":
                b = EventBlock(
                    name=bd["name"],
                    start=datetime.fromisoformat(bd["start"]),
                    duration=timedelta(minutes=bd["duration"]),
                    location=bd.get("location"),
                    notes=bd.get("notes"),
                    is_fixed=bool(bd.get("is_fixed", False)),
                    colour=colour,
                    priority=int(bd.get("priority", 0)),
                    repeatable=bool(bd.get("repeatable", False)),
                    interval=int(bd.get("interval", 0))
                )
            else:
                b = Task(
                    name=bd["name"],
                    start=datetime.fromisoformat(bd["start"]),
                    duration=timedelta(minutes=bd["duration"]),
                    deadline=datetime.fromisoformat(bd["deadline"]) if bd.get("deadline") else None,
                    location=bd.get("location"),
                    notes=bd.get("notes"),
                    is_fixed=bool(bd.get("is_fixed", False)),
                    colour=colour
                )
                b.is_completed = bd.get("is_completed", False)
                if b.is_completed and bd.get("completed_at"):
                    b.completed_at = datetime.fromisoformat(bd["completed_at"])
            self.blocks.append(b)

    # retrieval
    def day(self, day_date: datetime) -> List:
        """return all blocks on a specific day"""
        if isinstance(day_date, datetime):
            day_date = day_date.date()
        return [b for b in self.blocks if b.start.date() == day_date]

    def week(self, week_start: datetime) -> List:
        """return all blocks for the week starting with the given Monday"""
        while week_start.strftime("%A") != "Monday":
            week_start -= timedelta(days=1)
        return [b for b in self.blocks if week_start <= b.start.date() < week_start + timedelta(days=7)]

    def month(self, month_start: datetime) -> List:
        """return all blocks for the 5-week period starting from the Monday of the first week"""
        while month_start.strftime("%A") != "Monday":
            month_start -= timedelta(days=1)
        return [b for b in self.blocks if month_start <= b.start.date() < month_start + timedelta(days=35)]

    # modifications
    def add_block(self, b) -> None:
        """add block and update schedule"""
        self.blocks.append(b)
        if b.start is not None and b.type == "task":
            self.global_edf_scheduler(ignore_blocks=[b])
        else:
            self.global_edf_scheduler()

    def remove_block(self, b) -> None:
        """remove the real block from schedule"""
        real_block = next(
            (block for block in self.blocks
            if block is b or (block.name == b.name and block.start == b.start)),
            None
        )
        if real_block:
            self.blocks.remove(real_block)
            print(f"[DEBUG] Deleted block: {real_block.name}")
            self.global_edf_scheduler
        else:
            print(f"[DEBUG] Could not find block to delete: {b.name}")

    def mark_complete(self, t) -> None:
        """mark task as complete"""
        if t in self.blocks:
            t.mark_complete()
        self.global_edf_scheduler()

    def mark_incomplete(self, t) -> None:
        """mark task as incomplete"""
        if t in self.blocks:
            t.mark_incomplete()
        self.global_edf_scheduler()

    def clear_for_time(self, duration: Union[timedelta, str]) -> None:
        """clear schedule for the given duration starting now"""
        now = datetime.now()
        if duration == "rest of day":
            tomorrow = now + timedelta(days=1)
            start_time, _ = self.settings.get_day_bounds(tomorrow)
        else:
            start_time = now + duration
            _, end_time = self.settings.get_day_bounds(now)
            if start_time > end_time:
                tomorrow = now + timedelta(days=1)
                start_time, _ = self.settings.day_bounds(tomorrow)
        self.global_edf_scheduler(pointer=start_time)

    def clear_history(self) -> None:
        """
        removes blocks from schedule.blocks that are older than
        settings.history_duration (in days)
        """

        history_days = self.settings.history_duration
        cutoff = datetime.now() - history_days

        for b in self.blocks[:]:
            if (b.type == 'event' or b.type == 'task' and b.is_completed) and b.start < cutoff:
                self.blocks.remove(b)


    # scheduler
    def global_edf_scheduler(self, pointer: Optional[datetime] = None, ignore_blocks: Optional[List] = None) -> None:
        """schedule tasks globally using EDF, placing meals and breaks as needed"""
        SPECIAL_NAMES = ["breakfast", "lunch", "dinner", "break"]
        BREAK_INTERVAL = self.settings.break_interval
        BREAK_DURATION = self.settings.break_duration
        MEAL_DURATION = self.settings.meal_duration

        # helper functions
        def find_next_available(start_time: datetime, duration: timedelta, current_schedule: list) -> datetime:
            """
            finds earliest start time >= start_time to fit a block of duration, avoiding all fixed events 
            and already scheduled tasks/specials
            """

            current = start_time
            while True:
                conflict = False
                day_start, day_end = self.settings.get_day_bounds(current)
                if current < day_start:
                    current = day_start
                if current + duration > day_end:
                    # move to next day start
                    next_day = current + timedelta(days=1)
                    next_day_start, _ = self.settings.get_day_bounds(next_day)
                    current = datetime.combine(next_day.date(), next_day_start.time())
                    continue

                for b in current_schedule:
                    b_start = b.start
                    b_end = b.start + b.duration
                    # check overlap
                    if current < b_end and current + duration > b_start:
                        conflict = True
                        current = b_end
                        break

                if not conflict:
                    return current

        def ensure_meals_for_date(date: date, current_schedule: list) -> None:
            """ensure breakfast, lunch, dinner exist for the given date"""

            for meal_name in ["breakfast", "lunch", "dinner"]:
                # check if the meal already exists
                exists = any(
                    b.name.lower() == meal_name and b.start.date() == date
                    for b in current_schedule
                )
                if exists:
                    continue

                # filter blocks on that day that might conflict
                day_blocks = sorted(
                    [b for b in current_schedule if b.start is not None and b.start.date() == date],
                    key=lambda b: b.start
                )

                # meal window for that meal
                meal_start_time, meal_end_time = self.settings.meal_windows[meal_name]
                pointer = datetime.combine(date, meal_start_time)
                meal_window_end = datetime.combine(date, meal_end_time) - MEAL_DURATION

                # try to fit the meal in the window
                while pointer <= meal_window_end:
                    conflict = False
                    for b in day_blocks:
                        b_start = b.start
                        b_end = b.start + b.duration
                        # if the meal overlaps this block, move pointer to end of block
                        if pointer < b_end and pointer + MEAL_DURATION > b_start:
                            pointer = b_end
                            conflict = True
                            break
                    if not conflict:
                        # place the meal
                        meal_block = Task(
                            name=meal_name,
                            start=pointer,
                            duration=MEAL_DURATION,
                        )
                        current_schedule.append(meal_block)
                        break  # meal scheduled
                    # otherwise loop continues with updated pointer

        def meal_valid(meal_name: str, scheduled_blocks: list, pointer: datetime) -> bool:
            day_blocks = [b for b in scheduled_blocks if b.start is not None and b.start.date() == pointer.date()]
            meal_start, meal_end = self.settings.meal_windows[meal_name]
            meal_start = datetime.combine(pointer.date(), meal_start)
            meal_end = datetime.combine(pointer.date(), meal_end) - MEAL_DURATION
            if any(b.name == meal_name for b in day_blocks) or not(meal_start <= pointer <= meal_end):
                return False
            return True
        
        def break_valid(pointer: datetime, scheduled_blocks: list) -> bool:
            """determines if a break can be scheduled at 'pointer' on that day"""
            day_start, day_end = self.settings.get_day_bounds(pointer)
            if pointer + BREAK_DURATION > day_end:
                return False  # break won't fit before end of day

            # get only blocks for the same day
            day_blocks = [b for b in scheduled_blocks if b.start.date() == pointer.date()]
            day_blocks.sort(key=lambda b: b.start)

            # check backward: has enough time passed since last break (including meals)
            duration_since_last_break = timedelta(0)
            for b in reversed(day_blocks):
                if b.start >= pointer:
                    continue  # only consider blocks before pointer
                if b.name in {"break", "breakfast", "lunch", "dinner"}:
                    return False  # recent break or meal found
                duration_since_last_break += b.duration
                if duration_since_last_break >= BREAK_INTERVAL:
                    break

            # check forward: ensure break won't overlap future blocks
            for b in day_blocks:
                if b.start >= pointer + BREAK_DURATION:
                    break  # no conflict with this or future blocks
                if pointer < b.start + b.duration and pointer + BREAK_DURATION > b.start:
                    return False  # overlap detected

            return True


        # deep copy if needed to avoid mutating original list
        scheduled_blocks = self.blocks[:]

        # separate tasks, events, and special blocks
        ignore_blocks = ignore_blocks if ignore_blocks else []
        tasks = [
            b for b in scheduled_blocks
            if b.type == 'task' and not b.is_completed and not b.name in SPECIAL_NAMES and b not in ignore_blocks
        ]
        completed_tasks = [
            b for b in scheduled_blocks
            if b.type == 'task' and b.is_completed and not b.name in SPECIAL_NAMES and b not in ignore_blocks
        ]
        events = [b for b in scheduled_blocks if isinstance(b, EventBlock)]
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
                        # check if an event with the same name and start already exists
                        exists = any(
                            existing.name == b.name and existing.start == next_start
                            for existing in current_schedule
                        )
                        if not exists:
                            repeated_event = EventBlock(
                                name=b.name,
                                start=next_start,
                                duration=b.duration,
                                location=getattr(b, "location", None),
                                notes=getattr(b, "notes", None),
                                colour=b.colour(),
                                is_fixed=b.is_fixed,
                                priority=b.priority,
                                repeatable=b.repeatable,
                                interval=b.interval
                            )
                            current_schedule.append(repeated_event)
                    next_start += repeat_interval

        current_schedule = current_schedule + ignore_blocks
        current_schedule.sort(key=lambda b: b.start)

        # sort tasks by earliest deadline (EDF)
        tasks.sort(key=lambda t: t.deadline)
        # schedule tasks
        meal_names = ["breakfast", "lunch", "dinner"]
        pointer = pointer if pointer else datetime.now()
        for t in tasks:
            t.start = find_next_available(pointer, t.duration, current_schedule)
            pointer = t.start + t.duration
            current_schedule.append(t)
            meal_placed = False
            for i in meal_names:
                possible_start = find_next_available(pointer, MEAL_DURATION, current_schedule)
                if meal_valid(i, current_schedule, possible_start):
                    meal = Task(
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
                    break_block = Task(
                        name = "break",
                        start = possible_start,
                        duration = BREAK_DURATION,
                    )
                    current_schedule.append(break_block)
                    pointer = possible_start + BREAK_DURATION 
            
        all_dates = set()
        for b in current_schedule:
            # use the block's start if it exists, otherwise use its deadline date
            if b.start is not None:
                all_dates.add(b.start.date())
            elif hasattr(b, 'deadline') and b.deadline is not None:
                all_dates.add(b.deadline.date())
        for date in all_dates:
            ensure_meals_for_date(date, current_schedule)

        self.blocks = current_schedule + completed_tasks


