import pytest
import random
from datetime import datetime, timedelta, time

from schedule import Schedule
from blocks import Task, EventBlock


# =====================================================
# EDF-capable dummy settings
# =====================================================
class DummyEDFSettings:
    break_interval = timedelta(minutes=90)
    break_duration = timedelta(minutes=15)
    meal_duration = timedelta(minutes=30)
    history_duration = timedelta(days=7)

    meal_windows = {
        "breakfast": (time(7, 0), time(9, 0)),
        "lunch": (time(12, 0), time(14, 0)),
        "dinner": (time(18, 0), time(20, 0)),
    }

    def get_day_bounds(self, dt):
        start = datetime.combine(dt.date(), time(7, 0))
        end = datetime.combine(dt.date(), time(22, 0))
        return start, end

    def is_holiday(self, dt):
        return False


@pytest.fixture
def schedule():
    return Schedule(DummyEDFSettings())


# =====================================================
# Helper invariants
# =====================================================
def assert_no_overlap(blocks):
    blocks = sorted(blocks, key=lambda b: b.start)
    for a, b in zip(blocks, blocks[1:]):
        assert a.start + a.duration <= b.start, (
            f"Overlap: {a.name} overlaps {b.name}"
        )


def assert_within_day_bounds(schedule, blocks):
    for b in blocks:
        day_start, day_end = schedule.settings.get_day_bounds(b.start)
        assert day_start <= b.start
        assert b.start + b.duration <= day_end


# =====================================================
# Deterministic EDF tests
# =====================================================
def test_edf_orders_tasks_by_deadline(schedule):
    base = datetime(2026, 1, 3, 9, 0)

    t1 = Task("T1", base, timedelta(minutes=30), deadline=base + timedelta(hours=4))
    t2 = Task("T2", base, timedelta(minutes=30), deadline=base + timedelta(hours=1))
    t3 = Task("T3", base, timedelta(minutes=30), deadline=base + timedelta(hours=2))

    for t in [t1, t2, t3]:
        schedule.add_block(t)

    tasks = [
        b for b in schedule.blocks
        if b.type == "task" and b.name.startswith("T")
    ]

    assert [t.name for t in tasks] == ["T2", "T3", "T1"]


def test_edf_respects_fixed_event(schedule):
    base = datetime(2026, 1, 3, 9, 0)

    event = EventBlock(
        "Lecture",
        start=base + timedelta(hours=1),
        duration=timedelta(hours=2),
        is_fixed=True
    )

    task = Task(
        "Urgent",
        base,
        timedelta(minutes=60),
        deadline=base + timedelta(hours=2)
    )

    schedule.add_block(event)
    schedule.add_block(task)

    assert_no_overlap([event, task])


# =====================================================
# Boundary / edge-case EDF tests
# =====================================================
def test_task_with_deadline_in_past_not_scheduled_in_past(schedule):
    now = datetime.now()

    task = Task(
        "Past deadline",
        now,
        timedelta(minutes=30),
        deadline=now - timedelta(hours=1)
    )

    schedule.add_block(task)

    assert task.start >= now


def test_task_pushed_to_next_day_if_needed(schedule):
    late = datetime.combine(datetime.now().date(), time(21, 30))

    task = Task(
        "Large task",
        late,
        timedelta(hours=2),
        deadline=late + timedelta(hours=6)
    )

    schedule.add_block(task)

    assert_within_day_bounds(schedule, [task])


# =====================================================
# Invariant tests (critical)
# =====================================================
def test_no_task_overlap_under_edf(schedule):
    now = datetime.now()

    for i in range(6):
        schedule.add_block(Task(
            f"T{i}",
            now,
            timedelta(minutes=45),
            deadline=now + timedelta(hours=i + 1)
        ))

    tasks = [b for b in schedule.blocks if b.type == "task"]
    assert_no_overlap(tasks)


def test_completed_tasks_not_rescheduled(schedule):
    task = Task(
        "Completed",
        datetime.now(),
        timedelta(minutes=30),
        deadline=datetime.now() + timedelta(hours=2)
    )

    schedule.add_block(task)
    schedule.mark_complete(task)

    old_start = task.start
    schedule.global_edf_scheduler()

    assert task.start == old_start


# =====================================================
# Meals & breaks behaviour
# =====================================================
def test_meals_do_not_overlap_tasks(schedule):
    task = Task(
        "Long task",
        datetime.now(),
        timedelta(hours=4),
        deadline=datetime.now() + timedelta(hours=6)
    )

    schedule.add_block(task)

    meals = [
        b for b in schedule.blocks
        if b.name.lower() in {"breakfast", "lunch", "dinner"}
    ]

    for meal in meals:
        assert_no_overlap([meal, task])


def test_breaks_respect_break_interval(schedule):
    now = datetime.now()

    for i in range(3):
        schedule.add_block(Task(
            f"T{i}",
            now,
            timedelta(minutes=60),
            deadline=now + timedelta(hours=i + 2)
        ))

    breaks = [
        b for b in schedule.blocks
        if b.name.lower() == "break"
    ]

    breaks = sorted(breaks, key=lambda b: b.start)

    for a, b in zip(breaks, breaks[1:]):
        gap = b.start - (a.start + a.duration)
        assert gap >= schedule.settings.break_interval


# =====================================================
# Adversarial / fuzz testing
# =====================================================
def test_edf_fuzz_no_overlaps(schedule):
    base = datetime(2026, 1, 3, 8, 0)

    for i in range(25):
        start = base + timedelta(minutes=random.randint(0, 300))
        duration = timedelta(minutes=random.choice([15, 30, 45, 60]))
        deadline = start + timedelta(minutes=random.randint(30, 300))

        schedule.add_block(Task(
            f"R{i}",
            start,
            duration,
            deadline
        ))

    tasks = [
        b for b in schedule.blocks
        if b.type == "task" and not b.is_completed
    ]

    assert_no_overlap(tasks)
