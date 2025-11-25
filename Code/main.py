from classes import PersistenceManager, Schedule, ToDoList, Settings #and UI

def main():
    # Initialize components
    persistence_manager = PersistenceManager('data.json', 'settings.json')
    schedule = Schedule(date=None)  # date can be set later
    todo_list = ToDoList()
    settings = Settings()
    #ui = UI(schedule, todo_list, settings)

    # Load existing data
    data = persistence_manager.load_data()
    settings_data = persistence_manager.load_settings()
    if data:
        schedule.blocks = data.get('schedule_blocks', [])
        todo_list.tasks = data.get('todo_tasks', [])
    if settings: 
        settings.preferences = settings_data.get('settings', {})

    # Application logic would go here

    # Save current state before exiting
    data_to_save = {
        'schedule_blocks': schedule.blocks,
        'todo_tasks': todo_list.tasks,
        'settings': settings.preferences
    }
    persistence_manager.save_data(data_to_save)

if __name__ == "__main__":
    main()