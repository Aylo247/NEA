from datetime import datetime, timedelta

"""
This module defines the core classes for managing time blocks in a scheduling application.
It includes a base Block class and specialized Event and Task classes, as well as a 
CustomBlock class for handling user-defined block templates.
"""


#the base block class that other block types inherit from
class Block(): 
    def __init__(
            self,
            name, 
            start, 
            duration, 
            location = None, 
            notes = None , 
            is_fixed = False,
            colour = None
            ):
        self.name = name  #e.g., "Doctor Appointment", "Study Session"
        self.start = start #datetime object
        self.duration = duration #timedelta object
        self.location = location #e.g., "Room 101", "Downtown Clinic"
        self.notes = notes #additional details
        self.is_fixed = is_fixed #True if the block cannot be moved or resized
        self.colour = colour #hex colour code for UI representation

    @property
    def end(self):
        return self.duration + self.start #datetime object

#the event block that is fixed and cannot be moved
class eventblock(Block):

    def __init__(self, 
                name, 
                start, 
                duration, 
                location = "", 
                notes = "" , 
                is_fixed = True,
                colour = None, 
                priority = 0, 
                repeatable = False, 
                interval = 0):
        super().__init__(name, start, duration, location, notes, is_fixed, colour)
        self.priority = priority #0 for lowest and 2 for highest, for exambple a doctor appointment would be 2 but a lesson would be 1
        self.repeatable = repeatable
        self.type = "event"
        self.interval = interval

#the task block that is movable and can be marked complete or incomplete
class task(Block):
    def __init__(self, 
                 name,
                 start, 
                 duration, 
                 deadline=None, 
                 location = "", 
                 notes = "" , 
                 is_fixed = False,
                 colour = None):
        super().__init__(name, start, duration, location, notes, is_fixed, colour)
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
#note that when in use, the custom block can be treated like a normal event or task block so we dont really
#need any special methods in the logic of the schedule or when saving the schedule etc.
class CustomBlocks():
    def __init__(self, templates=None):
        self.templates = templates if templates is not None else []

    def add_template(self, template):
        """Add fixed-field template to memory."""
        self.templates.append(template)

    def delete_template(self, name):
        """Remove template by name."""
        self.templates = [t for t in self.templates if t["name"] != name]

    def instantiate(self, template_name, **overrides):
        """
        Create a block from a template.
        Only fixed fields from template are included; editable fields come from overrides.
        """
        template = next((t for t in self.templates if t["name"] == template_name), None)
        if not template:
            raise ValueError("Template not found")

        # Merge fixed fields from template with editable overrides
        params = template.copy()
        params.update(overrides)

        # Ensure start/duration exist
        start = params.get("start", datetime.now())
        duration = params.get("duration", timedelta(minutes=params.get("duration", 60)))

        if params.get("type") == "event":
            return eventblock(
                name=params["name"],
                start=start,
                duration=timedelta(minutes=duration),
                location=params.get("location", ""),
                notes=params.get("notes", ""),
                is_fixed=bool(params.get("is_fixed", True)),
                colour=params.get("colour", None),
                priority=int(params.get("priority", 0)),
                repeatable=bool(params.get("repeatable", False)),
                interval=int(params.get("interval", 0))
            )
        elif params.get("type") == "task":
            return task(
                name=params["name"],
                start=start,
                duration=timedelta(minutes=duration),
                deadline=params.get("deadline"),
                location=params.get("location", ""),
                notes=params.get("notes", ""),
                is_fixed=bool(params.get("is_fixed", False)),
                colour=params.get("colour", None)
            )
        else:
            raise ValueError("Unknown block type")

    