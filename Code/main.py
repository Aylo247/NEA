# """ from persitencemanager import PersistenceManager
# from schedule import Schedule
# from settings import Settings, ThemeManager
# from blocks import task, event
# from UI import MainWindow
# from datetime import datetime, timedelta
# from PyQt5.QtWidgets import QApplication
# from utils import GUIUtils
# import sys

# def main():
#     app = QApplication(sys.argv)

#     # Initialize schedule
#     schedule = Schedule()

#     # Add some test tasks and events
#     schedule.add_block(task(
#         name="Task 1",
#         start=datetime.now(),
#         duration=timedelta(minutes=45),
#         deadline=datetime.now() + timedelta(days=1),
#         location="Room 101",
#         notes="This is a test task"
#     ))

#     schedule.add_block(task(
#         name="Task 2",
#         start=datetime.now() + timedelta(days=2),  # no start time
#         duration=timedelta(minutes=30),
#         deadline=datetime.now() + timedelta(days=2)
#     ))  

#     schedule.add_block(event(
#         name="Doctor Appointment",
#         start=datetime.now() + timedelta(hours=2),
#         duration=timedelta(minutes=60),
#         location="Downtown Clinic",
#         notes="Annual checkup"
#     ))

#     # Initialize settings and persistence
#     settings = Settings()
#     persistence_manager = PersistenceManager()
#     data = persistence_manager.load_settings()
#     settings.from_dict(data)
#     thememanager = ThemeManager()  # use your real persistence
#     util = GUIUtils(thememanager, settings)

#     # Create main window
#     window = MainWindow(schedule, settings, persistence_manager, util)
#     window.show()

#     sys.exit(app.exec_())

# if __name__ == "__main__":
#     main() 
#  """
from datetime import datetime, timedelta
from blocks import task, event
from schedule import Schedule
from settings import Settings
from collections import Counter

# --- Initialize settings ---
settings = Settings()
sched = Schedule(settings)

# --- Add fixed events (2 weeks) ---
fixed_events = [
    ("Doctor Appointment", datetime(2025, 12, 23, 10, 0), 60, 2),
    ("Math Class", datetime(2025, 12, 23, 13, 0), 90, 1),
    ("Client Meeting", datetime(2025, 12, 23, 15, 0), 45, 2),
    ("Workshop", datetime(2025, 12, 24, 10, 0), 90, 1),
    ("Gym", datetime(2025, 12, 24, 16, 0), 60, 1),
    ("Concert", datetime(2025, 12, 24, 19, 30), 120, 1),
    ("Doctor Follow-up", datetime(2025, 12, 25, 9, 30), 30, 2),
    ("Team Meeting", datetime(2025, 12, 25, 11, 0), 60, 1),
    ("Lunch with Friend", datetime(2025, 12, 25, 13, 0), 60, 1),
    ("Team Call", datetime(2025, 12, 25, 17, 0), 60, 1),
    ("Project Presentation", datetime(2025, 12, 26, 14, 0), 60, 1),
    ("Workshop", datetime(2025, 12, 27, 10, 0), 120, 1),
    ("Gym", datetime(2025, 12, 28, 16, 0), 60, 1),
    ("Client Meeting", datetime(2025, 12, 29, 15, 0), 45, 2),
    ("Seminar", datetime(2025, 12, 30, 11, 0), 90, 1),
    ("Concert", datetime(2025, 12, 31, 19, 0), 120, 1),
    ("Doctor Appointment", datetime(2026, 1, 2, 9, 30), 30, 2),
    ("Team Meeting", datetime(2026, 1, 3, 11, 0), 60, 1),
    ("Workshop", datetime(2026, 1, 4, 10, 0), 120, 1),
    ("Gym", datetime(2026, 1, 5, 16, 0), 60, 1)
]

for name, start, duration_min, priority in fixed_events:
    sched.add_block(event(name, start, timedelta(minutes=duration_min), is_fixed=True, priority=priority))

# --- Add flexible tasks (2 weeks) ---
flexible_tasks = [
    ("Draft Proposal", datetime(2025, 12, 23, 18, 30), 60),
    ("Organize Files", datetime(2025, 12, 23, 20, 0), 45),
    ("Study Physics", datetime(2025, 12, 24, 12, 30), 90),
    ("Update Portfolio", datetime(2025, 12, 24, 15, 30), 60),
    ("Bake Cookies", datetime(2025, 12, 25, 10, 30), 45),
    ("Clean Garage", datetime(2025, 12, 25, 14, 30), 60),
    ("Write Journal", datetime(2025, 12, 25, 19, 30), 30),
    ("Research Topic", datetime(2025, 12, 26, 12, 0), 90),
    ("Prepare Slides", datetime(2025, 12, 26, 16, 0), 60),
    ("Draft Email Campaign", datetime(2025, 12, 27, 14, 0), 45),
    ("Study Chemistry", datetime(2025, 12, 28, 12, 0), 60),
    ("Update CV", datetime(2025, 12, 28, 18, 0), 45),
    ("Clean Room", datetime(2025, 12, 29, 14, 0), 60),
    ("Write Blog Post", datetime(2025, 12, 29, 18, 0), 90),
    ("Organize Photos", datetime(2025, 12, 30, 15, 0), 60),
    ("Study Maths", datetime(2025, 12, 31, 12, 0), 90),
    ("Plan Trip", datetime(2026, 1, 1, 10, 0), 120),
    ("Write Proposal", datetime(2026, 1, 2, 16, 0), 60),
    ("Review Notes", datetime(2026, 1, 3, 14, 0), 45),
    ("Update Portfolio", datetime(2026, 1, 4, 18, 0), 60),
    ("Draft Report", datetime(2026, 1, 5, 12, 0), 90)
]

for name, deadline, duration_min in flexible_tasks:
    sched.add_block(task(name=name, start=None, duration=timedelta(minutes=duration_min), deadline=deadline))

# --- Run initial EDF scheduler ---
sched.global_edf_scheduler()

# --- Print full detailed schedule ---
print("\n=== Full Schedule Detailed View ===")
for block in sorted(sched.blocks, key=lambda b: b.start):
    start_str = block.start.strftime("%Y-%m-%d %H:%M") if block.start else "N/A"
    end_str = (block.start + block.duration).strftime("%H:%M") if block.start else "N/A"
    deadline = getattr(block, "deadline", None)
    deadline_str = deadline.strftime("%Y-%m-%d %H:%M") if deadline else "N/A"
    status = "(Completed)" if getattr(block, "is_completed", False) else ""
    print(f"{start_str} - {end_str} | Deadline: {deadline_str} | {block.name} {status}")

# --- Meals / Breaks summary per day ---
meal_names = ["breakfast", "lunch", "dinner"]
for date in sorted({b.start.date() for b in sched.blocks if b.start}):
    meals_today = [b.name.lower() for b in sched.blocks if b.start.date() == date and b.name.lower() in meal_names]
    breaks_today = [b for b in sched.blocks if b.start.date() == date and b.name.lower() == "break"]
    print(f"\n{date} -> Meals: {Counter(meals_today)}, Breaks: {len(breaks_today)}")

# --- Mark some tasks as completed ---
completed_task_names = ["Draft Proposal", "Organize Files", "Bake Cookies", "Clean Garage"]
for b in sched.blocks:
    if isinstance(b, task) and b.name in completed_task_names:
        sched.mark_complete(b)

# --- Add new tasks ---
new_tasks = [
    ("Prepare Presentation Slides", datetime(2025, 12, 26, 18, 0), 60),
    ("Call Client", datetime(2025, 12, 27, 16, 0), 30),
    ("Buy Groceries", datetime(2025, 12, 28, 10, 0), 45),
    ("Practice Piano", datetime(2025, 12, 29, 17, 0), 45),
    ("Write Weekly Report", datetime(2026, 1, 2, 14, 0), 90)
]

for name, deadline, duration_min in new_tasks:
    sched.add_block(task(name=name, start=None, duration=timedelta(minutes=duration_min), deadline=deadline))

# --- Run EDF scheduler again ---
sched.global_edf_scheduler()

# --- Print full detailed schedule ---
print("\n=== Full Schedule Detailed View ===")
for block in sorted(sched.blocks, key=lambda b: b.start):
    start_str = block.start.strftime("%Y-%m-%d %H:%M") if block.start else "N/A"
    end_str = (block.start + block.duration).strftime("%H:%M") if block.start else "N/A"
    deadline = getattr(block, "deadline", None)
    deadline_str = deadline.strftime("%Y-%m-%d %H:%M") if deadline else "N/A"
    status = "(Completed)" if getattr(block, "is_completed", False) else ""
    print(f"{start_str} - {end_str} | Deadline: {deadline_str} | {block.name} {status}")

# --- Meals / Breaks summary per day ---
meal_names = ["breakfast", "lunch", "dinner"]
for date in sorted({b.start.date() for b in sched.blocks if b.start}):
    meals_today = [b.name.lower() for b in sched.blocks if b.start.date() == date and b.name.lower() in meal_names]
    breaks_today = [b for b in sched.blocks if b.start.date() == date and b.name.lower() == "break"]
    print(f"\n{date} -> Meals: {Counter(meals_today)}, Breaks: {len(breaks_today)}")

    
