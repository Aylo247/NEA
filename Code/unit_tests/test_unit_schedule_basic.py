import pytest
from datetime import datetime, timedelta, time

from schedule import Schedule
from blocks import Task, EventBlock


# ==========================
# Dummy Settings (non-EDF)
# ==========================
class DummySettings:
    # --- required by Schedule / EDF ---
    break_interval = timedelta(minutes=90)
    break_duration = timedelta(minutes=15)
    meal_duration = timedelta(minutes=30)

    meal_windows = {
        "breakfast": (time(7, 0), time(9, 0)),
        "lunch": (time(12, 0), time(14, 0)),
        "dinner": (time(18, 0), time(20, 0)),
    }

    history_duration = timedelta(days=7)

    def get_day_bounds(self, dt):
        start = datetime.combine(dt.date(), time(7, 0))
        end = datetime.combine(dt.date(), time(22, 0))
        return start, end

    def is_holiday(self, dt):
        return False



@pytest.fixture
def schedule():
    return Schedule(DummySettings())


# ==========================
# Basic Schedule behaviour
# ==========================

def test_add_block(schedule):
    task = Task(
        name="Maths",
        start=datetime.now(),
        duration=timedelta(minutes=45),
        deadline=datetime.now() + timedelta(hours=2)
    )

    schedule.add_block(task)

    assert task in schedule.blocks


def test_remove_block(schedule):
    task = Task(
        "Physics",
        datetime.now(),
        timedelta(minutes=30),
        deadline=datetime.now() + timedelta(hours=1)
    )

    schedule.add_block(task)
    schedule.remove_block(task)

    assert task not in schedule.blocks


def test_day_retrieval(schedule):
    today = datetime.now()

    task = Task(
        "Chemistry",
        today,
        timedelta(minutes=40),
        deadline=today + timedelta(hours=3)
    )

    schedule.add_block(task)

    day_blocks = schedule.day(today)

    assert task in day_blocks


def test_week_retrieval(schedule):
    monday = datetime(2026, 1, 5, 9, 0)  # known Monday

    task = Task(
        "Biology",
        monday,
        timedelta(minutes=50),
        deadline=monday + timedelta(hours=2)
    )

    schedule.add_block(task)

    week_blocks = schedule.week(monday)

    assert task in week_blocks


def test_month_retrieval(schedule):
    date = datetime(2026, 1, 3, 10, 0)

    task = Task(
        "English",
        date,
        timedelta(minutes=60),
        deadline=date + timedelta(hours=3)
    )

    schedule.add_block(task)

    month_blocks = schedule.month(date)

    assert task in month_blocks


def test_mark_complete(schedule):
    task = Task(
        "History",
        datetime.now(),
        timedelta(minutes=30),
        deadline=datetime.now() + timedelta(hours=1)
    )

    schedule.add_block(task)
    schedule.mark_complete(task)

    assert task.is_completed is True
    assert isinstance(task.completed_at, datetime)


def test_mark_incomplete(schedule):
    task = Task(
        "Geography",
        datetime.now(),
        timedelta(minutes=30),
        deadline=datetime.now() + timedelta(hours=1)
    )

    schedule.add_block(task)
    schedule.mark_complete(task)
    schedule.mark_incomplete(task)

    assert task.is_completed is False
    assert task.completed_at is None


def test_clear_history_removes_old_completed_tasks(schedule):
    old_date = datetime.now() - timedelta(days=10)

    task = Task(
        "Old task",
        old_date,
        timedelta(minutes=30),
        deadline=old_date + timedelta(hours=1)
    )

    task.is_completed = True

    schedule.blocks.append(task)
    schedule.clear_history()

    assert task not in schedule.blocks


# ==========================
# Persistence (non-algorithmic)
# ==========================

def test_to_dict_from_dict_cycle(schedule):
    task = Task(
        "Persisted",
        datetime.now(),
        timedelta(minutes=45),
        deadline=datetime.now() + timedelta(hours=2)
    )

    event = EventBlock(
        "Meeting",
        datetime.now() + timedelta(hours=3),
        timedelta(hours=1),
        is_fixed=True
    )

    schedule.add_block(task)
    schedule.add_block(event)

    data = schedule.to_dict()

    new_schedule = Schedule(DummySettings())
    new_schedule.from_dict(data)

    assert len(new_schedule.blocks) == 2
    assert {b.name for b in new_schedule.blocks} == {"Persisted", "Meeting"}

def test_clear_for_rest_of_day_calls_scheduler_with_next_day_start(schedule):
    captured = {}

    def fake_scheduler(pointer=None, ignore_blocks=None):
        captured["pointer"] = pointer

    # spy on EDF call
    schedule.global_edf_scheduler = fake_scheduler

    schedule.clear_for_time("rest of day")

    tomorrow = datetime.now() + timedelta(days=1)
    expected_start, _ = schedule.settings.get_day_bounds(tomorrow)

    assert captured["pointer"].date() == expected_start.date()
    assert captured["pointer"].time() == expected_start.time()

def test_clear_for_time_within_same_day(schedule):
    captured = {}

    def fake_scheduler(pointer=None, ignore_blocks=None):
        captured["pointer"] = pointer

    schedule.global_edf_scheduler = fake_scheduler

    delta = timedelta(hours=2)
    before = datetime.now()

    schedule.clear_for_time(delta)

    # allow tiny execution delay
    assert captured["pointer"] >= before + delta

