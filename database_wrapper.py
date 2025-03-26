"""
Database Management Module

This script manages user, message, and settings databases stored in JSON files. It ensures
that required directories exist, handles missing or corrupted files gracefully, and resets
specific user fields upon loading.

Key Features:
- Automatically creates the database directory if it does not exist.
- Loads JSON-based databases safely, initializing default values when necessary.
- Resets user login states and address fields on startup to ensure consistency.
- Supports structured message storage with separate lists for undelivered and delivered messages.
- Maintains a settings file for application-wide configuration values.

Last Updated: February 12, 2025
"""

import json
import os


# Define database file paths
users_database_path = lambda id: f"database/users_{id}.json"  # noqa: E731
messages_database_path = lambda id: f"database/messages_{id}.json"  # noqa: E731
settings_database_path = lambda id: f"database/settings_{id}.json"  # noqa: E731


def safe_load(filepath, default_value):
    """
    Safely loads a JSON file. If the file is missing or contains invalid JSON, it
    initializes the file with a default value and returns that instead.
    """
    try:
        with open(filepath, "r") as file:
            return json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        with open(filepath, "w") as file:
            json.dump(default_value, file)
        return default_value


def load_database(vm_id):
    """
    Loads user, message, and settings databases from JSON files.
    """
    users, messages, settings = None, None, None

    # Create the database folder if it does not exist
    if not os.path.exists("database"):
        os.makedirs("database")

    # Load users with safe default
    users = safe_load(users_database_path(vm_id), {})

    for user in users:
        if users[user]["logged_in"]:
            users[user]["logged_in"] = False
            users[user]["addr"] = None

    # Load messages with safe default
    messages = safe_load(
        messages_database_path(vm_id), {"undelivered": [], "delivered": []}
    )

    # Load settings with safe default
    settings = safe_load(
        settings_database_path(vm_id),
        {
            "counter": 0,
            "host": "127.0.0.1",
            "port": 54400,
            "host_json": "127.0.0.1",
            "port_json": 54444,
        },
    )

    return users, messages, settings


def load_client_database(vm_id):
    """
    Loads user, message, and settings databases from JSON files for the client.
    """
    settings = None

    if not os.path.exists("database"):
        raise Exception("Database directory does not exist.")

    settings = safe_load(
        settings_database_path(vm_id),
        {
            "counter": 0,
            "host": "127.0.0.1",
            "port": 54400,
            "host_json": "127.0.0.1",
            "port_json": 54444,
        },
    )

    return settings


def save_database(vm_id, users, messages, settings):
    """
    Saves user, message, and settings data back to JSON files.
    """
    with open(users_database_path(vm_id), "w") as users_file:
        json.dump(users, users_file)
    with open(messages_database_path(vm_id), "w") as messages_file:
        json.dump(messages, messages_file)
    with open(settings_database_path(vm_id), "w") as settings_file:
        json.dump(settings, settings_file)


def reset_database(vm_id):
    """
    Resets the database by clearing all user and message data.
    """
    users = {}
    messages = {"undelivered": [], "delivered": []}
    settings = {
        "counter": 0,
        "host": "127.0.0.1",
        "port": 54400,
        "host_json": "127.0.0.1",
        "port_json": 54444,
    }

    save_database(vm_id, users, messages, settings)
    return users, messages, settings
