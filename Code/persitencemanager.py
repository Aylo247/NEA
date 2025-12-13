import json
           
"""
The PersistenceManager class handles saving and loading data and settings to and from JSON files.
"""

class PersistenceManager:
    def __init__(self):
        self.data_file = "data.json"
        self.settings_file = "settings.json"
        self.custom_blocks_file = "custom_blocks.json"
        self.themes_file = "themes.json"

    #saves and loads custom block templates
    def load_custom_blocks(self):
        try:
            with open(self.custom_blocks_file, "r") as f:
                json_data = f.read()
                data = json.loads(json_data)
                return data.get('Templates', [])
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_custom_blocks(self, custom_blocks):
        if custom_blocks is None:
            return None
        data_to_save = {}
        if custom_blocks is not None:
            data_to_save['Templates'] = custom_blocks

        json_data = json.dumps(data_to_save, indent=4)
        with open(self.custom_blocks_file, 'w') as f:
            f.write(json_data)
        


    #saves and loads settings
    def save_settings(self, settings):
        if settings is None:
            return None
        data_to_save = {}
        if settings is not None:
            data_to_save['settings'] = settings.to_dict()
        
        json_data = json.dumps(data_to_save, indent=4)
        with open(self.settings_file, 'w') as f:
            f.write(json_data)

    def load_settings(self):
        try:
            with open(self.settings_file, 'r') as f:
                json_data = f.read()
                data = json.loads(json_data)
                return data.get('settings', {})
        except (FileNotFoundError, json.JSONDecodeError):
            return {}


    #saves and loads schedule data
    def save_data(self, schedule=None):
        if schedule is None:
            return None
        data_to_save = {}
        if schedule is not None:
            data_to_save['schedule'] = schedule.to_dict()
        
        json_data = json.dumps(data_to_save, indent=4)
        with open(self.data_file, 'w') as f:
            f.write(json_data)

    def load_data(self):
        try:
            with open(self.data_file, 'r') as f:
                json_data = f.read()
                data = json.loads(json_data)
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            return {}


    #a convenience method to save both schedule and settings at once
    def save_all(self, schedule, settings, custom_blocks):

        self.save_custom_blocks(custom_blocks)
        self.save_data(schedule)
        self.save_settings(settings)