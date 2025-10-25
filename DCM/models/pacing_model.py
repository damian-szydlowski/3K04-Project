# models/pacing_model.py
import json
import os
from typing import Dict, Any

# Get the absolute path to the 'models' directory
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(_CURRENT_DIR, "pacing_settings.json")

def _load_settings_file() -> Dict[str, Any]:
    """Loads the pacing settings dictionary from the JSON file."""
    if not os.path.exists(SETTINGS_FILE):
        return {}
    try:
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_settings_file(data: Dict[str, Any]) -> None:
    """Saves the pacing settings dictionary to the JSON file."""
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=2)

class PacingModel:
    def __init__(self):
        """
        Loads all pacing settings for all users.
        The data structure looks like:
        {
            "username1": {
                "AOO": {"param": "value", ...},
                "VVI": {"param": "value", ...}
            },
            "username2": {
                "AOO": {"param": "value", ...}
            }
        }
        """
        self.settings = _load_settings_file()

    def load_settings(self, username: str, mode: str) -> Dict[str, str]:
        """
        Loads the specific parameters for a given user and mode.
        Returns an empty dict if no settings are found.
        """
        user_settings = self.settings.get(username, {})
        mode_settings = user_settings.get(mode, {})
        return mode_settings

    def save_settings(self, username: str, mode: str, data: Dict[str, str]):
        """
        Saves the specific parameters for a given user and mode.
        """
        # Ensure the user's dictionary exists
        if username not in self.settings:
            self.settings[username] = {}
        
        # Set the data for that mode
        self.settings[username][mode] = data
        
        # Save the entire settings object back to the file
        _save_settings_file(self.settings)