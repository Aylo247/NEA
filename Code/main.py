from classes import PersistenceManager, Schedule, ToDoList, Settings 
from UI import MainWindow

def main():
    # Initialize components
    persistence_manager = PersistenceManager('data.json', 'settings.json')
    schedule = Schedule()
    todo_list = ToDoList()
    settings = Settings()
    ui = MainWindow(schedule, todo_list, settings, persistence_manager)


    data = persistence_manager.load_data()
    settings_data = persistence_manager.load_settings()
    if data:
        schedule.blocks = data.get('schedule_blocks', [])
        todo_list.tasks = data.get('todo_tasks', [])
    if settings: 
        settings.preferences = settings_data.get('settings', {})

    # Application logic would go here
    ui.switch_to_scheduleDay()

    # Save current state before exiting
    
    settings_to_save = {
        'settings': settings.preferences,
    }
    persistence_manager.save_settings(settings_to_save)

if __name__ == "__main__":
    main() 
