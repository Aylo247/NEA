from classes import PersistenceManager, Schedule, ToDoList, Settings 
from UI import MainWindow
from PyQt5.QtWidgets import QApplication
import sys

def main():
    # Initialise core classes
    persistence_manager = PersistenceManager('data.json', 'settings.json')
    schedule = Schedule()
    todo_list = ToDoList()
    settings = Settings()

    # --- Load data BEFORE creating UI ---
    data = persistence_manager.load_data()
    settings_data = persistence_manager.load_settings()

    if data:
        schedule.from_dict(data.get("schedule", {}))
        todo_list.from_dict(data.get("todo", {}))

    if settings_data:
        settings.preferences = settings_data.get('settings', {})

    # --- Create QApplication ---
    app = QApplication(sys.argv)

    # --- Create MainWindow after data is loaded ---
    ui = MainWindow(schedule, todo_list, settings, persistence_manager)

    # ui.switch_to_scheduleDay()
    ui.show()

    # --- Start Qt Event Loop ---
    result = app.exec()

    # --- Save settings before exit ---
    settings_to_save = {
        'settings': settings.preferences,
    }
    persistence_manager.save_settings(settings_to_save)

    sys.exit(result)


if __name__ == "__main__":
    main() 
