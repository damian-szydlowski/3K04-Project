import json
import os
from typing import Tuple

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
USER_FILE = os.path.join(_CURRENT_DIR, "users.json")

MAX_USERS = 3

def _load_users() -> dict:
    """Loads the user dictionary from the JSON file."""
    if not os.path.exists(USER_FILE):
        return {}
    try:
        with open(USER_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_users(users: dict) -> None:
    """Saves the user dictionary to the JSON file."""
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=2)

class UserModel:
    def __init__(self):
        # The dictionary stores: username -> password
        self.users = _load_users()  

    def get_user_count(self) -> int:
        return len(self.users)
        
    def register_user(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Registers a new user with a plaintext password.
        Returns (success: bool, message: str)
        """
        username = username.strip()
        if not username or not password:
            return False, "Both fields are required."

        if len(self.users) >= MAX_USERS:
            return False, "User limit reached. Maximum of 10 users."

        if username in self.users:
            return False, "That username is already registered."

        self.users[username] = password
        
        _save_users(self.users)
        return True, f"User '{username}' registered."

    def authenticate(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Authenticates a user against the plaintext password.
        Returns (success: bool, message: str)
        """
        username = username.strip()
        
        # Get the stored password for the user
        stored_password = self.users.get(username)
        
        if not stored_password:
            return False, "Invalid username or password."

        # Do a simple string comparison
        if password == stored_password:
            return True, "Login successful."
        else:
            return False, "Invalid username or password."