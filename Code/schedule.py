from datetime import datetime, timedelta, date, time
from typing import List, Optional, Union
from blocks import Task, EventBlock
from PyQt5.QtGui import QColor

class ScheduleInfeasibleError(Exception):
    def __init__(self, task, missing_minutes):
        self.task = task
        self.missing_minutes = missing_minutes
        super().__init__(
            f"Task '{task.name}' cannot be scheduled before its deadline "
            f"(missing {missing_minutes} minutes)."
        )

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
            if b.name.lower() in {"breakfast", "lunch", "dinner", "break"}:
                continue
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
        if isinstance(week_start, datetime):
            week_start = week_start.date()

        while week_start.strftime("%A") != "Monday":
            week_start -= timedelta(days=1)

        return [
            b for b in self.blocks
            if week_start <= b.start.date() < week_start + timedelta(days=7)
        ]

    def month(self, month_start: datetime) -> List:
        """return all blocks for the 5-week period starting from the Monday of the first week"""
        if isinstance(month_start, datetime):
            month_start = month_start.date()

        while month_start.strftime("%A") != "Monday":
            month_start -= timedelta(days=1)

        return [
            b for b in self.blocks
            if month_start <= b.start.date() < month_start + timedelta(days=35)
        ]

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
        """Schedule tasks globally using EDF. If infeasible, raise ScheduleInfeasibleError.
        Meals and breaks are added only after a feasible task schedule exists.
        """
        SPECIAL_NAMES = {"breakfast", "lunch", "dinner", "break"}
        BREAK_INTERVAL = self.settings.break_interval
        BREAK_DURATION = self.settings.break_duration
        MEAL_DURATION = self.settings.meal_duration

        # --------------------------
        # helper functions
        # --------------------------
        def find_next_available(start_time: datetime, duration: timedelta, current_schedule: list) -> datetime:
            """Earliest start >= start_time that fits duration within day bounds and avoids overlaps."""
            current = start_time
            while True:
                day_start, day_end = self.settings.get_day_bounds(current)
                if current < day_start:
                    current = day_start

                if current + duration > day_end:
                    # move to next day start
                    next_day = current + timedelta(days=1)
                    next_day_start, _ = self.settings.get_day_bounds(next_day)
                    current = datetime.combine(next_day.date(), next_day_start.time())
                    continue

                # overlap check with all scheduled blocks
                conflict_found = False
                for b in current_schedule:
                    b_start = b.start
                    b_end = b.start + b.duration
                    if current < b_end and current + duration > b_start:
                        current = b_end
                        conflict_found = True
                        break

                if not conflict_found:
                    return current

        def ensure_meals_for_date(day: date, current_schedule: list) -> None:
            """Ensure breakfast/lunch/dinner exist for the given date (best-effort)."""
            for meal_name in ["breakfast", "lunch", "dinner"]:
                exists = any(
                    b.name.lower() == meal_name and b.start.date() == day
                    for b in current_schedule
                    if b.start is not None
                )
                if exists:
                    continue

                day_blocks = sorted(
                    [b for b in current_schedule if b.start is not None and b.start.date() == day],
                    key=lambda b: b.start
                )

                meal_start_time, meal_end_time = self.settings.meal_windows[meal_name]
                probe = datetime.combine(day, meal_start_time)
                latest_start = datetime.combine(day, meal_end_time) - MEAL_DURATION

                while probe <= latest_start:
                    # if overlaps any block, jump probe to end of that block and retry
                    moved = False
                    for b in day_blocks:
                        if probe < b.start + b.duration and probe + MEAL_DURATION > b.start:
                            probe = b.start + b.duration
                            moved = True
                            break
                    if moved:
                        continue

                    # place meal
                    current_schedule.append(Task(name=meal_name, start=probe, duration=MEAL_DURATION))
                    break

        def break_valid(at_time: datetime, scheduled_blocks: list) -> bool:
            """Whether a break can be scheduled at at_time on that day (best-effort)."""
            day_start, day_end = self.settings.get_day_bounds(at_time)
            if at_time + BREAK_DURATION > day_end:
                return False

            day_blocks = [b for b in scheduled_blocks if b.start is not None and b.start.date() == at_time.date()]
            day_blocks.sort(key=lambda b: b.start)

            # backward check: ensure BREAK_INTERVAL since last break/meal
            duration_since_last_break = timedelta(0)
            for b in reversed(day_blocks):
                if b.start >= at_time:
                    continue
                if b.name.lower() in {"break", "breakfast", "lunch", "dinner"}:
                    return False
                duration_since_last_break += b.duration
                if duration_since_last_break >= BREAK_INTERVAL:
                    break

            # forward check: no overlap
            for b in day_blocks:
                if b.start >= at_time + BREAK_DURATION:
                    break
                if at_time < b.start + b.duration and at_time + BREAK_DURATION > b.start:
                    return False

            return True

        # --------------------------
        # Feasibility check (tasks + fixed events only)
        # --------------------------
        def available_minutes_between(start: datetime, end: datetime, fixed_events: list) -> int:
            """Working minutes between start and end, minus fixed events overlap."""
            if end <= start:
                return 0

            total = 0.0
            cursor = start

            while cursor < end:
                ds, de = self.settings.get_day_bounds(cursor)
                ws = max(cursor, ds)
                we = min(end, de)
                if we > ws:
                    total += (we - ws).total_seconds() / 60.0
                # next day midnight
                cursor = datetime.combine((cursor + timedelta(days=1)).date(), time(0, 0))

            # subtract fixed event overlaps
            for e in fixed_events:
                e_start = e.start
                e_end = e.start + e.duration
                os = max(start, e_start)
                oe = min(end, e_end)
                if oe > os:
                    total -= (oe - os).total_seconds() / 60.0

            return max(0, int(total))

        def check_feasible(tasks_only: list, fixed_events: list, start_time: datetime) -> tuple[bool, Optional[Task], Optional[int]]:
            """EDF feasibility: for each deadline D, sum(durations of tasks with deadline<=D) <= available_time(start..D)."""
            ordered = sorted(tasks_only, key=lambda t: (t.deadline or datetime.max))

            required_so_far = 0.0
            for t in ordered:
                if t.deadline is None:
                    # if you allow tasks without deadlines, decide policy.
                    # For now treat as "latest" so it never triggers infeasible.
                    continue

                required_so_far += t.duration.total_seconds() / 60.0
                available = available_minutes_between(start_time, t.deadline, fixed_events)

                if required_so_far > available:
                    missing = int(required_so_far - available)
                    return False, t, missing

            return True, None, None

        # --------------------------
        # Start of main logic
        # --------------------------
        scheduled_blocks = self.blocks[:]  # shallow copy

        ignore_blocks = ignore_blocks if ignore_blocks else []

        tasks = [
            b for b in scheduled_blocks
            if b.type == "task"
            and not b.is_completed
            and b.name.lower() not in SPECIAL_NAMES
            and b not in ignore_blocks
        ]

        completed_tasks = [
            b for b in scheduled_blocks
            if b.type == "task"
            and b.is_completed
            and b.name.lower() not in SPECIAL_NAMES
            and b not in ignore_blocks
        ]

        # base events (include repeat expansions as you had)
        events = [b for b in scheduled_blocks if isinstance(b, EventBlock)]
        current_schedule = [
            e for e in events
            if not (getattr(e, "repeatable", False) and self.settings.is_holiday(e.start))
        ]

        # expand repeatable events (kept close to your original)
        for b in list(current_schedule):
            if getattr(b, "repeatable", False):
                repeat_interval = timedelta(days=b.interval)
                next_start = b.start + repeat_interval
                while next_start <= datetime.now() + timedelta(days=42):
                    if not self.settings.is_holiday(next_start):
                        exists = any(existing.name == b.name and existing.start == next_start for existing in current_schedule)
                        if not exists:
                            repeated_event = EventBlock(
                                name=b.name,
                                start=next_start,
                                duration=b.duration,
                                location=getattr(b, "location", None),
                                notes=getattr(b, "notes", None),
                                colour=getattr(b, "colour", None),  # NOTE: your original used b.colour() which may be wrong
                                is_fixed=b.is_fixed,
                                priority=getattr(b, "priority", 0),
                                repeatable=True,
                                interval=b.interval
                            )
                            current_schedule.append(repeated_event)
                    next_start += repeat_interval

        # include ignore blocks (they should be treated as fixed for this run)
        current_schedule = current_schedule + ignore_blocks
        current_schedule.sort(key=lambda b: b.start)

        # pointer start
        start_pointer = pointer if pointer else datetime.now()

        # Feasibility pass #1 (no breaks/meals)
        feasible, failing_task, missing_minutes = check_feasible(tasks, current_schedule, start_pointer)
        if not feasible:
            # "rerun without breaks" is effectively the same because feasibility ignores breaks/meals.
            # Kept as the structure you want: second pass could relax other constraints if you add them later.
            feasible2, failing_task2, missing2 = check_feasible(tasks, current_schedule, start_pointer)
            if not feasible2:
                raise ScheduleInfeasibleError(
                    f"Schedule infeasible: '{failing_task2.name}' misses its deadline by ~{missing2} minutes.",
                    failing_task=failing_task2,
                    missing_minutes=missing2
                )

        # --------------------------
        # Place tasks with EDF (still no meals/breaks)
        # --------------------------
        tasks.sort(key=lambda t: (t.deadline or datetime.max))
        pointer_time = start_pointer

        for t in tasks:
            t.start = find_next_available(pointer_time, t.duration, current_schedule)
            current_schedule.append(t)
            pointer_time = t.start + t.duration  # pointer moves only because of tasks
            current_schedule.sort(key=lambda b: b.start)  # keep overlap checks simple

        # --------------------------
        # Decorate: meals (best-effort)
        # --------------------------
        all_dates = {b.start.date() for b in current_schedule if b.start is not None}
        for d in all_dates:
            ensure_meals_for_date(d, current_schedule)

        # --------------------------
        # Decorate: breaks (best-effort, never break feasibility)
        # --------------------------
        current_schedule.sort(key=lambda b: b.start)
        # try a break after each block end
        for b in list(current_schedule):
            candidate = b.start + b.duration
            if break_valid(candidate, current_schedule):
                current_schedule.append(Task(name="break", start=candidate, duration=BREAK_DURATION))
                current_schedule.sort(key=lambda x: x.start)

        # final assignment (keep completed tasks)
        self.blocks = current_schedule + completed_tasks

    def run_scheduler_with_feedback(schedule): #put in eveywhere
        try:
            schedule.global_edf_scheduler()
            return True, None

        except ScheduleInfeasibleError as e:
            info = {
                "task_name": e.failing_task.name if e.failing_task else "Unknown task",
                "missing_minutes": e.missing_minutes,
                "message": str(e)
            }
            return False, info

