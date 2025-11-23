from datetime import datetime, timedelta

def Block():
    def __init__(self, name, start, end, location = "", notes = "" , is_fixed = ""):
        self.name = name 
        self.start = start
        self.end = end
        self.location = location
        self.notes = notes
        self.is_fixed = is_fixed

    @property
    def duration(self):
        return self.end - self.start
    
    def edit(self):
        pass

    def delete(self):
        pass

    def move(self, new_start, new_end):
        if self.is_fixed:
            raise ValueError("Cannot move a fixed block.")
        self.start = new_start
        self.end = new_end


def event(Block):
    def __init__(self, name, start, end, priority = 0, location = "", notes = "" , is_fixed = True):
        super().__init__(name, start, end, location, notes, is_fixed)
        self.priority = priority

def task(Block):
    def __init__(self, name, start, end, deadline = None, location = "", notes = "" , is_fixed = False):
        super().__init__(name, start, end, location, notes, is_fixed)
        self.deadline = deadline
        self.is_completed = False

    def mark_complete(self):
        self.is_completed = True

    def auto_reschedule(self, new_start):
        if self.is_completed:
            return
        self.start = new_start
        self.end = new_start + self.duration