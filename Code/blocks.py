from datetime import datetime, timedelta
from typing import Optional, Union
from PyQt5.QtGui import QColor


class Block:
    """base class for all time blocks"""
    
    def __init__(
        self,
        name: str,
        start: datetime,
        duration: timedelta,
        location: Optional[str] = None,
        notes: Optional[str] = None,
        is_fixed: bool = False,
        colour: Optional[QColor] = None 
    ) -> None:
        self.name = name
        self.start = start
        self.duration = duration
        self.location = location
        self.notes = notes
        self.is_fixed = is_fixed
        self.colour = colour

    @property
    def end(self) -> datetime:
        """return the end datetime of the block"""
        return self.start + self.duration


class EventBlock(Block):
    """fixed, non-movable block representing scheduled events"""

    def __init__(
        self,
        name: str,
        start: datetime,
        duration: timedelta,
        location: str = "",
        notes: str = "",
        is_fixed: bool = True,
        colour: Optional[QColor] = None,
        priority: int = 0,
        repeatable: bool = False,
        interval: int = 0
    ) -> None:
        super().__init__(name, start, duration, location, notes, is_fixed, colour)
        self.priority = priority  # 0 = low, 2 = high
        self.repeatable = repeatable
        self.interval = interval
        self.type = "event"


class Task(Block):
    """movable block representing a task that can be completed"""

    def __init__(
        self,
        name: str,
        start: datetime,
        duration: timedelta,
        deadline: Optional[datetime] = None,
        location: str = "",
        notes: str = "",
        is_fixed: bool = False,
        colour: Optional[QColor] = None
    ) -> None:
        super().__init__(name, start, duration, location, notes, is_fixed, colour)
        self.deadline = deadline
        self.is_completed = False
        self.completed_at = None
        self.type = "task"

    def mark_complete(self) -> None:
        """mark the task as completed and timestamp it"""
        if not self.is_completed:
            self.is_completed = True
            self.completed_at = datetime.now()

    def mark_incomplete(self) -> None:
        """revert the task to incomplete and clear the timestamp"""
        if self.is_completed:
            self.is_completed = False
            self.completed_at = None


class CustomBlocks:
    """manage user-defined block templates for tasks and events"""

    def __init__(self, templates=None) -> None:
        self.templates = templates or []

    def add_template(self, template) -> None:
        """add a template to memory"""
        self.templates.append(template)

    def delete_template(self, name) -> None:
        """remove a template by name"""
        self.templates = [t for t in self.templates if t["name"] != name]

    def instantiate(self, template_name, **overrides) -> Union[Task, EventBlock]:
        """
        create a Block from a template, applying any overrides
        returns EventBlock or Task depending on the type
        """
        template = next((t for t in self.templates if t["name"] == template_name), None)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")

        params = {**template, **overrides}
        start = params.get("start", datetime.now())
        duration_value = params.get("duration", 60)
        duration = duration_value if isinstance(duration_value, timedelta) else timedelta(minutes=duration_value)

        if params.get("type") == "event":
            return EventBlock(
                name=params["name"],
                start=start,
                duration=duration,
                location=params.get("location", ""),
                notes=params.get("notes", ""),
                is_fixed=params.get("is_fixed", True),
                colour=params.get("colour"),
                priority=params.get("priority", 0),
                repeatable=params.get("repeatable", False),
                interval=params.get("interval", 0),
            )
        elif params.get("type") == "task":
            return Task(
                name=params["name"],
                start=start,
                duration=duration,
                deadline=params.get("deadline"),
                location=params.get("location", ""),
                notes=params.get("notes", ""),
                is_fixed=params.get("is_fixed", False),
                colour=params.get("colour"),
            )
        else:
            raise ValueError(f"unknown block type '{params.get('type')}'")
        
    def to_dict(self) -> dict:
        """serialize to dictionary"""
        return {"templates": self.templates}

    def from_dict(self, data: dict) -> None:
        """load templates from dictionary"""
        self.templates = data["templates"]