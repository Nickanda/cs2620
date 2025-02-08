import json
import os

users_database_path = "database/users.json"
messages_database_path = "database/messages.json"

def load_database():
    users, messages = None, None

    # Create the database folder if it does not exist
    if not os.path.exists("database"):
      os.makedirs("database")

    # If the files don't exist, create them!
    if not os.path.exists(users_database_path):
      with open(users_database_path, "w") as users_file:
        json.dump({}, users_file)
        users = {}
    # Otherwise, load in their information
    else:
      with open(users_database_path, "r") as users_file:
        users = json.load(users_file)

    # Repeat for the messages
    if not os.path.exists(messages_database_path):
      with open(messages_database_path, "w") as messages_file:
        json.dump({}, messages_file)
        messages = {
            "undelivered": [],
            "delivered": []
        }
    else:
      with open(messages_database_path, "r") as messages_file:
        messages = json.load(messages_file)

    return users, messages

def save_database(users, messages):
    with open(users_database_path, "w") as users_file:
        json.dump(users, users_file)
    with open(messages_database_path, "w") as messages_file:
        json.dump(messages, messages_file)