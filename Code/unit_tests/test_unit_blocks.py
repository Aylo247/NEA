import pytest
from datetime import datetime, timedelta

from blocks import EventBlock, Task


# ==================================================
# Abstract Block behaviour (via subclasses)
# ==================================================
def test_end_time_calculated_for_eventblock():
    start = datetime(2026, 1, 1, 9, 0)
    duration = timedelta(hours=2)

    event = EventBlock("Meeting", start, duration)

    assert event.end == datetime(2026, 1, 1, 11, 0)


def test_end_time_calculated_for_task():
    start = datetime(2026, 1, 1, 14, 0)
    duration = timedelta(minutes=45)

    task = Task("Revision", start, duration)

    assert task.end == datetime(2026, 1, 1, 14, 45)


# ==================================================
# EventBlock tests
# ==================================================
def test_eventblock_defaults():
    event = EventBlock(
        "Exam",
        datetime(2026, 1, 1, 10, 0),
        timedelta(hours=2)
    )

    assert event.is_fixed is True
    assert event.type == "event"


# ==================================================
# Task tests
# ==================================================
def test_task_completion_cycle():
    task = Task(
        "Essay",
        datetime.now(),
        timedelta(hours=1)
    )

    assert task.is_completed is False

    task.mark_complete()
    assert task.is_completed is True
    assert task.completed_at is not None

    task.mark_incomplete()
    assert task.is_completed is False
    assert task.completed_at is None
