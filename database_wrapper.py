import json
import os

users_database_path = "database/users.json"
messages_database_path = "database/messages.json"
settings_database_path = "database/settings.json"

def load_database():
    users, messages, settings = None, None, None

    # Create the database folder if it does not exist
    if not os.path.exists("database"):
        os.makedirs("database")

    # Function to load JSON safely
    def safe_load(filepath, default_value):
        try:
            with open(filepath, "r") as file:
                return json.load(file)
        except (json.JSONDecodeError, FileNotFoundError):
            with open(filepath, "w") as file:
                json.dump(default_value, file)
            return default_value

    # Load users with safe default
    users = safe_load(users_database_path, {})

    # Ensure logged_in and addr fields are reset
    for user in users:
        if users[user].get("logged_in", False):  # Use .get() to avoid KeyErrors
            users[user]["logged_in"] = False
            users[user]["addr"] = 0

    # Load messages with safe default
    messages = safe_load(messages_database_path, {
        "undelivered": [],
        "delivered": []
    })

    # Load settings with safe default
    settings = safe_load(settings_database_path, {
        "counter": 0
    })

    return users, messages, settings

def save_database(users, messages, settings):
    with open(users_database_path, "w") as users_file:
        json.dump(users, users_file)
    with open(messages_database_path, "w") as messages_file:
        json.dump(messages, messages_file)
    with open(settings_database_path, "w") as settings_file:
        json.dump(settings, settings_file)
