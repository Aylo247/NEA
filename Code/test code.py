from datetime import datetime, timedelta, time, date
from classes import event, task, Schedule, CustomBlock, ToDoList, Settings, PersistenceManager

pm = PersistenceManager()  # initialize persistence manager

# --- Create some events and tasks ---
e1 = event(
    name="Doctor Appointment",
    start=datetime(2025, 12, 11, 10, 0),
    duration=timedelta(minutes=30),
    location="Clinic",
    priority=2
)

t1 = task(
    name="Math Homework",
    start=datetime(2025, 12, 11, 15, 0),
    duration=timedelta(minutes=60),
    deadline=datetime(2025, 12, 12, 23, 59),
    notes="Chapter 5 exercises"
)

t2 = task(
    name="Physics Project",
    start=datetime(2025, 12, 12, 14, 0),
    duration=timedelta(minutes=120),
    notes="Build the prototype"
)

# --- Create a schedule and add blocks ---
sched = Schedule()
sched.add_block(e1)
sched.add_block(t1)
sched.add_block(t2)

# --- Test CustomBlock ---
cb = CustomBlock()
# Add Study Session template
study_template = {
    "type": "task",
    "name": "Study Session",
    "duration": 60,  # minutes
    "location": "Library",
    "notes": "",
    "is_fixed": False,
    "start": "2025-12-11T14:00:00"
}
cb.add_template(study_template)

study1 = cb.instantiate("Study Session")
study2 = cb.instantiate("Study Session", start="2025-12-11T16:00:00")

sched.add_block(study1)
sched.add_block(study2)

# Mark first as complete
study1.mark_complete()

# Move second into slot of completed one
study2.move(study1.start)

# --- Test ToDoList ---
todo = ToDoList()
todo.take_tasks_from_schedule(sched)

# --- Test Settings ---
settings = Settings()
settings.update(pm, theme="Dark", start_time=time(8,0))

# --- Save everything ---
pm.save_custom_blocks(cb.templates)
print("\nSaved schedule, settings, and custom blocks to JSON files.")

# --- Reload and verify ---
# Load custom blocks
loaded_templates = pm.load_custom_blocks()
print("\nLoaded custom block templates from file:")
for t in loaded_templates:
    print(t)

# Load schedule
loaded_data = pm.load_data()
loaded_sched = Schedule()
loaded_sched.from_dict(loaded_data.get("schedule", {}))
print("\nLoaded schedule from file:")
for b in loaded_sched.blocks:
    status = "completed" if getattr(b, "is_completed", False) else "pending"
    print(f"{b.type}: {b.name} from {b.start} to {b.end} [{status}]")

# Load settings
loaded_settings_data = pm.load_settings()
loaded_settings = Settings()
loaded_settings.from_dict(loaded_settings_data)
print(f"\nLoaded settings from file: theme={loaded_settings.theme}, start_time={loaded_settings.start_time}")
