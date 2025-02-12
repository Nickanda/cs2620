"""
Server Implementation for a User Messaging System (JSON Commands)

This script sets up a socket-based server that handles user registration,
login, searching for user accounts, sending messages, reading messages,
deleting messages, and deleting user accounts using JSON-based commands.
The server listens on a specified host and port, accepts new connections,
and parses incoming JSON data to perform requested operations.

Key functionalities include:
- Accepting new client connections and managing them with selectors
- Handling JSON commands for account creation, login, logout, search, etc.
- Tracking delivered and undelivered messages in a shared data structure
- Storing and retrieving user/messaging data via database_wrapper
- Implementing wildcard-based user search
- Handling message and account deletion requests

Last updated: February 12, 2025
"""

import socket
import selectors
import types
import database_wrapper
import fnmatch
import json

# Create a default selector for managing multiple sockets
sel = selectors.DefaultSelector()

HOST = "127.0.0.1"
PORT = 54444

users = None  # Holds user account information
messages = None  # Holds delivered and undelivered messages
settings = None  # Holds additional settings (like a message counter)


def accept_wrapper(sock):
    """
    Accept a new socket connection and register it with the selector.
    """
    conn, addr = sock.accept()
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)


def send_message(sock: socket.socket, command: str, data, message: str):
    """
    Send a message back to the client. The message is a string, typically
    prefixed with a short command name, followed by a JSON payload.
    """
    sock.send(("0 " + message).encode("utf-8"))
    data.outb = data.outb[len(command) :]


def send_error(sock: socket.socket, command: str, data, error_message: str):
    """
    Helper function to send an error message back to the client in JSON format.
    """
    error_obj = {"error": error_message}
    sock.send(("0 error " + json.dumps(error_obj)).encode("utf-8"))
    data.outb = data.outb[len(command) :]


def get_new_messages(username):
    """
    Return the number of undelivered messages for a specific user.
    """
    num_messages = 0
    for msg_obj in messages["undelivered"]:
        if msg_obj["receiver"] == username:
            num_messages += 1
    return num_messages


def service_connection(key, mask):
    """
    Process I/O for a client connection, reading JSON-based commands and
    sending corresponding responses or performing required actions.
    """
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        try:
            recv_data = sock.recv(1024)
        except ConnectionResetError:
            recv_data = None

        if recv_data:
            data.outb += recv_data
        else:
            # Client disconnected
            print(f"Closing connection to {data.addr}")
            sel.unregister(sock)
            sock.close()

            # Mark the corresponding user as logged out
            for user in users:
                if users[user]["addr"] == data.addr[1]:
                    users[user]["logged_in"] = False
                    users[user]["addr"] = 0
                    break

            database_wrapper.save_database(users, messages, settings)
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            # Decode the entire payload, split by space for the command,
            # then parse the rest as JSON
            words = data.outb.decode("utf-8").split(" ")
            version = words[0]
            command = " ".join(words)
            json_data = json.loads(" ".join(words[2:]))

            if version != "0":
                send_message(sock, command, data, "error Unsupported protocol version")
                return

            ###################################################################
            # Process recognized JSON-based commands.
            ###################################################################

            # Create command
            if words[1] == "create":
                username = json_data["username"].strip()
                password = json_data["password"].strip()

                if not username.isalnum():
                    send_error(sock, command, data, "Username must be alphanumeric")
                    return

                if username in users:
                    send_error(sock, command, data, "Username already exists")
                    return

                if password.strip() == "":
                    send_error(sock, command, data, "Password cannot be empty")
                    return

                # Create new user in the users dict
                users[username] = {
                    "password": password,
                    "logged_in": True,
                    "addr": data.addr[1],
                }

                return_dict = {"username": username, "undeliv_messages": 0}
                # Send a response indicating successful login with 0 unread messages
                send_message(sock, command, data, f"login {json.dumps(return_dict)}")
                database_wrapper.save_database(users, messages, settings)

            # Login command
            elif words[1] == "login":
                username = json_data["username"]
                password = json_data["password"]

                if username not in users:
                    send_error(sock, command, data, "Username does not exist")
                    return

                if users[username]["logged_in"]:
                    send_error(sock, command, data, "User already logged in")
                    return

                if password != users[username]["password"]:
                    send_error(sock, command, data, "Incorrect password")
                    return

                # Count undelivered messages
                num_messages = get_new_messages(username)

                # Mark as logged in
                users[username]["logged_in"] = True
                users[username]["addr"] = data.addr[1]

                return_dict = {"username": username, "undeliv_messages": num_messages}

                send_message(sock, command, data, f"login {json.dumps(return_dict)}")
                database_wrapper.save_database(users, messages, settings)

            # Logout command
            elif words[1] == "logout":
                username = json_data["username"]

                if username not in users:
                    send_error(sock, command, data, "Username does not exist")
                    return

                # Mark user as logged out
                users[username]["logged_in"] = False
                users[username]["addr"] = 0

                send_message(sock, command, data, "logout {}")
                database_wrapper.save_database(users, messages, settings)

            # Search command
            elif words[1] == "search":
                pattern = json_data["search"]
                matched_users = fnmatch.filter(users.keys(), pattern)

                return_dict = {"user_list": matched_users}

                send_message(
                    sock, command, data, f"user_list {json.dumps(return_dict)}"
                )

            # Delete account command
            elif words[1] == "delete_acct":
                acct = json_data["username"]

                if acct not in users:
                    send_error(sock, command, data, "Account does not exist")
                    return

                # Remove user
                del users[acct]

                # Also remove messages where this user is sender or receiver
                def del_acct_msgs(msg_obj_lst, acct):
                    msg_obj_lst[:] = [
                        msg_obj
                        for msg_obj in msg_obj_lst
                        if msg_obj["sender"] != acct and msg_obj["receiver"] != acct
                    ]

                del_acct_msgs(messages["delivered"], acct)
                del_acct_msgs(messages["undelivered"], acct)

                send_message(sock, command, data, "logout {}")
                database_wrapper.save_database(users, messages, settings)

            # Send message command
            elif words[1] == "send_msg":
                sender = json_data["sender"]
                receiver = json_data["recipient"]
                message = json_data["message"]

                if receiver not in users:
                    send_error(sock, command, data, "Receiver does not exist")
                    return

                # Increment the message counter
                settings["counter"] += 1
                msg_obj = {
                    "id": settings["counter"],
                    "sender": sender,
                    "receiver": receiver,
                    "message": message,
                }

                # Decide if message is delivered or undelivered based on receiver log-in status
                if users[receiver]["logged_in"]:
                    messages["delivered"].append(msg_obj)
                else:
                    messages["undelivered"].append(msg_obj)

                # Return the new count of undelivered messages for the sender
                num_messages = get_new_messages(sender)
                return_dict = {"undeliv_messages": num_messages}

                send_message(
                    sock, command, data, f"refresh_home {json.dumps(return_dict)}"
                )
                database_wrapper.save_database(users, messages, settings)

            elif words[1] == "get_undelivered":
                # user decides on the number of messages to view
                receiver = json_data["username"]  # i.e. logged in user
                num_msg_view = json_data["num_messages"]

                delivered_msgs = messages["delivered"]
                undelivered_msgs = messages["undelivered"]

                to_deliver = []
                remove_indices = []  # List to store indices to delete later

                if len(undelivered_msgs) == 0 and num_msg_view > 0:
                    send_error(sock, command, data, "No undelivered messages")
                    return

                # Move messages from undelivered to delivered
                for ind, msg_obj in enumerate(undelivered_msgs):
                    if num_msg_view == 0:
                        break

                    if msg_obj["receiver"] == receiver:
                        to_deliver.append(
                            {
                                "id": msg_obj["id"],
                                "sender": msg_obj["sender"],
                                "message": msg_obj["message"],
                            }
                        )
                        delivered_msgs.append(msg_obj)
                        remove_indices.append(
                            ind
                        )  # Store index instead of deleting in-place
                        num_msg_view -= 1

                # Delete from undelivered_msgs in reverse order to avoid index shifting
                for ind in sorted(remove_indices, reverse=True):
                    del undelivered_msgs[ind]

                return_dict = {"messages": to_deliver}

                send_message(sock, command, data, f"messages {json.dumps(return_dict)}")
                database_wrapper.save_database(users, messages, settings)

            # Get delivered messages
            elif words[1] == "get_delivered":
                # User decides on the number of messages to view
                receiver = json_data["username"]  # i.e. logged in user
                num_msg_view = json_data["num_messages"]

                delivered_msgs = messages["delivered"]

                if len(delivered_msgs) == 0 and num_msg_view > 0:
                    send_error(sock, command, data, "No delivered messages")
                    return

                to_deliver = []
                for ind, msg_obj in enumerate(delivered_msgs):
                    if num_msg_view == 0:
                        break

                    if msg_obj["receiver"] == receiver:
                        to_deliver.append(
                            {
                                "id": msg_obj["id"],
                                "sender": msg_obj["sender"],
                                "message": msg_obj["message"],
                            }
                        )

                        num_msg_view -= 1

                return_dict = {"messages": to_deliver}

                send_message(sock, command, data, f"messages {json.dumps(return_dict)}")

            # Refresh home command
            elif words[1] == "refresh_home":
                # Count up undelivered messages
                username = json_data["username"]

                num_messages = get_new_messages(username)

                return_dict = {"undeliv_messages": num_messages}

                send_message(
                    sock, command, data, f"refresh_home {json.dumps(return_dict)}"
                )

            # Delete message command
            elif words[1] == "delete_msg":
                current_user = json_data["current_user"]
                msgids_to_delete = set(json_data["delete_ids"].split(","))
                messages["delivered"] = [
                    msg
                    for msg in messages["delivered"]
                    if not (
                        str(msg["id"]) in msgids_to_delete
                        and msg["receiver"] == current_user
                    )
                ]

                num_messages = get_new_messages(current_user)

                return_dict = {"undeliv_messages": num_messages}

                send_message(
                    sock, command, data, f"refresh_home {json.dumps(return_dict)}"
                )
                database_wrapper.save_database(users, messages, settings)

            else:
                # Command not recognized
                print(f"No valid command: {command}")
                data.outb = data.outb[len(command) :]


if __name__ == "__main__":
    # Load data from the database at startup
    users, messages, settings = database_wrapper.load_database()

    HOST = settings["host_json"]
    PORT = settings["port_json"]

    # Create and bind the listening socket
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.bind((HOST, PORT))
    lsock.listen()
    print("Listening on", (HOST, PORT))
    lsock.setblocking(False)
    sel.register(lsock, selectors.EVENT_READ, data=None)
    try:
        while True:
            events = sel.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    # Accept new connections
                    accept_wrapper(key.fileobj)
                else:
                    # Service existing connections
                    service_connection(key, mask)
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")
        sel.close()
    finally:
        sel.close()
