import json
from typing import List, Optional, Dict, Any
from cryptography.fernet import Fernet, InvalidToken
import os

class PersistenceManager:
    """
    handles saving and loading of schedule data, settings, and custom block templates
    to/from JSON files
    """

    def __init__(self) -> None:
        self.data_file = "data.json"
        self.settings_file = "settings.json"
        self.custom_blocks_file = "custom_blocks.json"
        self.key_file = "secret.key"

        self.fernet = Fernet(self._load_or_create_key())

    # encryption helpers
    def _load_or_create_key(self) -> bytes:
        if not os.path.exists(self.key_file):
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(key)
            return key

        with open(self.key_file, "rb") as f:
            return f.read()

    def _encrypt(self, data: dict) -> bytes:
        json_bytes = json.dumps(data).encode("utf-8")
        return self.fernet.encrypt(json_bytes)

    def _decrypt(self, encrypted_data: bytes) -> dict:
        decrypted_bytes = self.fernet.decrypt(encrypted_data)
        return json.loads(decrypted_bytes.decode("utf-8"))

    # custom Block templates 
    def load_custom_blocks(self) -> list:
        """
        Loads and decrypts custom block templates from JSON file.
        Returns a list of templates, empty if file missing or corrupted.
        """
        try:
            with open(self.custom_blocks_file, "rb") as f:
                encrypted = f.read()
                decrypted = self._decrypt(encrypted)   # already a dict/list
                return decrypted.get("Templates")                       # no json.loads needed
        except (FileNotFoundError, InvalidToken):
            return []

    def save_custom_blocks(self, custom_blocks) -> None:
        """
        save encrypted custom block templates to JSON file
        if custom_blocks is None, does nothing
        """
        if custom_blocks is None:
            return

        data_to_save = {"Templates": custom_blocks.to_dict()}
        encrypted = self._encrypt(data_to_save)

        with open(self.custom_blocks_file, "wb") as f:
            f.write(encrypted)


    # settings 
    def save_settings(self, settings) -> None:
        """
        save settings object to JSON file
        expects settings to have a `to_dict()` method
        """
        if settings is None:
            return
        data_to_save = {'settings': settings.to_dict()}
        with open(self.settings_file, 'w') as f:
            json.dump(data_to_save, f, indent=4)

    def load_settings(self) -> Dict[str, Any]:
        """
        load settings from JSON file
        returns a dictionary of settings, empty if file missing or corrupted
        """
        try:
            with open(self.settings_file, 'r') as f:
                data = json.load(f)
                return data.get('settings', {})
        except (FileNotFoundError, InvalidToken):
            return {}


    # schedule data 
    def save_data(self, schedule) -> None:
        """
        saves encrypted schedule data to JSON file
        expects schedule to have a `to_dict()` method
        """
        if schedule is None:
            return

        data_to_save = {"schedule": schedule.to_dict()}
        encrypted = self._encrypt(data_to_save)

        with open(self.data_file, "wb") as f:
            f.write(encrypted)

    def load_data(self) -> Dict[str, Any]:
        try:
            with open(self.data_file, "rb") as f:
                encrypted = f.read()
                return self._decrypt(encrypted)
        except (FileNotFoundError, InvalidToken):
            return {}
 
    # Convenience Method 
    def save_all(self, schedule, settings, custom_blocks) -> None:
        """
        save schedule, settings, and custom blocks all at once
        """
        self.save_custom_blocks(custom_blocks)
        self.save_data(schedule)
        self.save_settings(settings)
