from persitencemanager import PersistenceManager
from schedule import Schedule
from settings import Settings, ThemeManager
from blocks import task, event
from UI import MainWindow
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QApplication
from utils import GUIUtils
import sys

def main():
    app = QApplication(sys.argv)

    # Initialize schedule
    schedule = Schedule()

    # Add some test tasks and events
    schedule.add_block(task(
        name="Task 1",
        start=datetime.now(),
        duration=timedelta(minutes=45),
        deadline=datetime.now() + timedelta(days=1),
        location="Room 101",
        notes="This is a test task"
    ))

    schedule.add_block(task(
        name="Task 2",
        start=datetime.now() + timedelta(days=2),  # no start time
        duration=timedelta(minutes=30),
        deadline=datetime.now() + timedelta(days=2)
    ))  

    schedule.add_block(event(
        name="Doctor Appointment",
        start=datetime.now() + timedelta(hours=2),
        duration=timedelta(minutes=60),
        location="Downtown Clinic",
        notes="Annual checkup"
    ))

    # Initialize settings and persistence
    settings = Settings()
    persistence_manager = PersistenceManager()
    data = persistence_manager.load_settings()
    settings.from_dict(data)
    thememanager = ThemeManager()  # use your real persistence
    util = GUIUtils(thememanager, settings)

    # Create main window
    window = MainWindow(schedule, settings, persistence_manager, util)
    window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 

