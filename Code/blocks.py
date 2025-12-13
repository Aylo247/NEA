from datetime import datetime, timedelta

"""
This module defines the core classes for managing time blocks in a scheduling application.
It includes a base Block class and specialized Event and Task classes, as well as a 
CustomBlock class for handling user-defined block templates.
"""


#the base block class that other block types inherit from
class Block(): 
    def __init__(self, name, start, duration, location = None, notes = None , is_fixed = False):
        self.name = name  #e.g., "Doctor Appointment", "Study Session"
        self.start = start #datetime object
        self.duration = duration #timedelta object
        self.location = location #e.g., "Room 101", "Downtown Clinic"
        self.notes = notes #additional details
        self.is_fixed = is_fixed #True if the block cannot be moved or resized

    @property
    def end(self):
        return self.duration + self.start #datetime object
    
    def edit(self,**kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key): # check if attribute exists
                setattr(self, key, value)

    def move(self, new_start):
        if self.is_fixed:
            raise ValueError("Cannot move a fixed block.") #error should display a pop-up in the GUI
        self.start = new_start

#the event block that is fixed and cannot be moved
class event(Block):

    def __init__(self, name, start, duration, location = "", notes = "" , is_fixed = True, priority = 0, repeatable = False, interval = 0):
        super().__init__(name, start, duration, location, notes, is_fixed)
        self.priority = priority #0 for lowest an 2 for highest, for exambple a doctor appointment would be 2 but a lesson would be 1
        self.repeatable = repeatable
        self.type = "event"
        self.repeatinterval = interval

#the task block that is movable and can be marked complete or incomplete
class task(Block):
    def __init__(self, name, start, duration, deadline = None, location = "", notes = "" , is_fixed = False):
        super().__init__(name, start, duration, location, notes, is_fixed)
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
class CustomBlock():
    def __init__(self, templates = None):
        self.templates = templates if templates is not None else []

    #adds\removes custom block templates from only the in-memory list, not the actual file, that only happens when save() is called
    def add_template(self, template):
        self.templates.append(template)

    def delete_template(self, name):
        self.templates = [t for t in self.templates if t["name"] != name]

    #instantiates a block from a template with optional overrides
    def instantiate(self, template_name, **kwargs):
        template = next((t for t in self.templates if t["name"] == template_name), None)
        if not template:
            raise ValueError("Template not found")

        params = template.copy()
        params.update(kwargs)
        
        if params.get("type") == "event":
            name = params.get("name") 
            start = datetime.fromisoformat(params.get("start"))
            duration = timedelta(minutes=params.get("duration"))

            location = params.get("location", "")
            notes = params.get("notes", "")
            is_fixed = bool(params.get("is_fixed", True))
            priority = int(params.get("priority", 0))
            repeatable = bool(params.get("repeatable", False))
            interval = int(params.get("interval") if repeatable else 0)
            return event(name, start, duration, location, notes, is_fixed, priority, repeatable, interval)
        
        elif params.get("type") == "task":
            name = params.get("name")
            start = datetime.fromisoformat(params.get("start"))
            duration = timedelta(minutes=params.get("duration"))
            deadline = params.get("deadline", None)
            location = params.get("location", "")
            notes = params.get("notes", "")
            is_fixed = bool(params.get("is_fixed", False))
            return task(name, start, duration, deadline, location, notes, is_fixed)
        
        else:
            raise ValueError("Unknown block type")
    