"""
Server Implementation for a User Messaging System (Plaintext Commands)

This script sets up a socket-based server that handles user registration,
login, searching for user accounts, sending messages, reading messages,
deleting messages, and deleting user accounts using plaintext commands.
The server listens on a specified host and port, accepts new connections,
and processes incoming commands from connected clients.

Key functionalities include:
- Accepting new client connections and registering them with selectors
- Parsing commands for creating accounts, logging in/out, sending messages, etc.
- Tracking delivered and undelivered messages in a shared data structure
- Storing and retrieving user/messaging data via database_wrapper
- Implementing wildcard-based user search
- Handling message deletion, account deletion, and other operations

Last updated: February 12, 2025
"""

import socket
import selectors
import types
import database_wrapper
import fnmatch

# Create a default selector for managing multiple sockets
sel = selectors.DefaultSelector()

HOST = "127.0.0.1"
PORT = 54400

###############################################################################
# Specifications for the project
###############################################################################
# 1: Creating an account. The user supplies a unique (login) name. If there is already an account with that name, the user is prompted for the password. If the name is not being used, the user is prompted to supply a password. The password should not be passed as plaintext.
# 2: Log in to an account. Using a login name and password, log into an account. An incorrect login or bad user name should display an error. A successful login should display the number of unread messages.
# 3: List accounts, or a subset of accounts that fit a text wildcard pattern. If there are more accounts than can comfortably be displayed, allow iterating through the accounts.
# 4. Send a message to a recipient. If the recipient is logged in, deliver immediately; if not the message should be stored until the recipient logs in and requests to see the message.
# 5: Read messages. If there are undelivered messages, display those messages. The user should be able to specify the number of messages they want delivered at any single time.
# 6. Delete a message or set of messages. Once deleted messages are gone.
# 7. Delete an account. You will need to specify the semantics of deleting an account that contains unread messages.
# ------------------------------------------------------------------------------

users = None  # Holds user account information, login status, etc.
messages = None  # Holds delivered and undelivered messages
settings = None  # Holds additional settings like a message counter


def accept_wrapper(sock):
    """
    Accept a new socket connection from a client and register it with the selector.
    """
    conn, addr = sock.accept()
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    # SimpleNamespace is used here to attach arbitrary attributes to 'data'
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    # Register for both read and write events
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)


def send_message(sock: socket.socket, command: str, data, message: str):
    """
    Send a message back to the client. The message is encoded into bytes and appended
    to the outb buffer, which will be flushed when the socket is ready to write.
    """
    sock.send(("0 " + message).encode("utf-8"))
    # Trim the command portion from the outb buffer
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
    Handle the I/O for a client connection. This includes reading incoming data
    and parsing commands, then sending appropriate responses or performing
    specified actions (e.g., user creation, login, message sending).
    """
    sock = key.fileobj  # The socket object
    data = key.data  # The data namespace for the socket

    if mask & selectors.EVENT_READ:
        try:
            recv_data = sock.recv(1024)
        except ConnectionResetError:
            recv_data = None

        if recv_data:
            data.outb += recv_data
        else:
            # If no data is received, the client has disconnecte
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
            # If we have outgoing data to send
            words = data.outb.decode("utf-8").split(" ")
            version = words[0]
            command = " ".join(words)

            if version != "0":
                send_message(sock, command, data, "error Unsupported protocol version")
                return

            ###################################################################
            # Below are various commands processed by the server.
            ###################################################################

            # Account creation command
            if words[1] == "create":
                username = words[2]
                username.strip()
                password = " ".join(words[3:])

                if not username.isalnum():
                    send_message(
                        sock, command, data, "error Username must be alphanumeric"
                    )
                    return

                if username in users:
                    send_message(sock, command, data, "error Username already exists")
                    return

                if password.strip() == "":
                    send_message(sock, command, data, "error Password cannot be empty")
                    return

                # Create new user record
                users[username] = {
                    "password": password,
                    "logged_in": True,
                    "addr": data.addr[1],
                }

                # Notify client of successful login, with zero unread messages
                send_message(sock, command, data, f"login {username} 0")

                # Persist changes to the database
                database_wrapper.save_database(users, messages, settings)

            # Login command
            elif words[1] == "login":
                username = words[2]
                password = " ".join(words[3:]).strip()

                if username not in users:
                    send_message(sock, command, data, "error Username does not exist")
                    return

                if users[username]["logged_in"]:
                    send_message(sock, command, data, "error User already logged in")
                    return

                if password != users[username]["password"]:
                    send_message(sock, command, data, "error Incorrect password")
                    return

                # Calculate the number of undelivered messages for this user
                num_messages = 0
                for msg_obj in messages["undelivered"]:
                    if msg_obj["receiver"] == username:
                        num_messages += 1

                # Mark user as logged in
                users[username]["logged_in"] = True
                users[username]["addr"] = data.addr[1]

                # Notify client of successful login and undelivered message count
                send_message(sock, command, data, f"login {username} {num_messages}")

                # Persist changes
                database_wrapper.save_database(users, messages, settings)

            # Logout command
            elif words[1] == "logout":
                username = words[2]

                if username not in users:
                    send_message(sock, command, data, "error Username does not exist")
                    return

                # Mark user as logged out
                users[username]["logged_in"] = False
                users[username]["addr"] = 0

                send_message(sock, command, data, "logout")
                database_wrapper.save_database(users, messages, settings)

            # Search command
            elif words[1] == "search":
                # If no pattern is provided, assume wildcard '*'
                pattern = words[2] if len(words) > 1 else "*"
                matched_users = fnmatch.filter(users.keys(), pattern)

                # Return a space-separated list of matched users
                send_message(
                    sock, command, data, f"user_list {' '.join(matched_users)}"
                )

            # Delete account command
            elif words[1] == "delete_acct":
                acct = words[2]

                if acct not in users:
                    send_message(sock, command, data, "error Account does not exist")
                    return

                # Remove the user from the users dictionary
                del users[acct]

                # Remove any messages (delivered or undelivered) from or to this account
                def del_acct_msgs(msg_obj_lst, acct):
                    msg_obj_lst[:] = [
                        msg_obj
                        for msg_obj in msg_obj_lst
                        if msg_obj["sender"] != acct and msg_obj["receiver"] != acct
                    ]

                del_acct_msgs(messages["delivered"], acct)
                del_acct_msgs(messages["undelivered"], acct)

                # Notify client to log out
                send_message(sock, command, data, "logout")
                database_wrapper.save_database(users, messages, settings)

            # Send message command
            elif words[1] == "send_msg":
                # The command format is 'send_msg sender receiver message...'
                sender = words[2]
                receiver = words[3]
                message = " ".join(words[4:])

                if receiver not in users:
                    send_message(sock, command, data, "error Receiver does not exist")
                    return

                # Replace any null-character placeholders to avoid issues
                message = message.replace("\0", "NULL")

                # Increment message counter in settings
                settings["counter"] += 1
                msg_obj = {
                    "id": settings["counter"],
                    "sender": sender,
                    "receiver": receiver,
                    "message": message,
                }

                # If receiver is logged in, move to delivered messages immediately
                if users[receiver]["logged_in"]:
                    messages["delivered"].append(msg_obj)
                else:
                    # Otherwise, store it in undelivered
                    messages["undelivered"].append(msg_obj)

                # Refresh the home screen of the sender with updated unread co
                num_messages = get_new_messages(sender)
                send_message(sock, command, data, f"refresh_home {num_messages}")

                # Save to database
                database_wrapper.save_database(users, messages, settings)

            # Get undelivered messages command
            elif words[1] == "get_undelivered":
                # Format: 'get_undelivered receiver num_messages'
                receiver = words[2]

                # Validate that number of messages is an integer
                if words[3].isdigit():
                    num_msg_view = int(words[3])
                else:
                    send_message(
                        sock,
                        command,
                        data,
                        "error Number of messages to view must be an integer",
                    )
                    return

                delivered_msgs = messages["delivered"]
                undelivered_msgs = messages["undelivered"]

                to_deliver = []
                remove_indices = []

                # If no undelivered messages but the client wants to view some
                if len(undelivered_msgs) == 0 and num_msg_view > 0:
                    send_message(sock, command, data, "error No undelivered messages")
                    return

                # Move messages from 'undelivered' to 'delivered'
                for ind, msg_obj in enumerate(undelivered_msgs):
                    if num_msg_view == 0:
                        break

                    if msg_obj["receiver"] == receiver:
                        to_deliver.append(
                            f"{msg_obj['id']}_{msg_obj['sender']}_{msg_obj['message']}"
                        )
                        delivered_msgs.append(msg_obj)
                        remove_indices.append(ind)
                        num_msg_view -= 1

                # Remove them from undelivered in reverse index order
                for ind in sorted(remove_indices, reverse=True):
                    del undelivered_msgs[ind]

                # Send messages to the client separated by a null-like character
                send_message(sock, command, data, ("messages " + "\0".join(to_deliver)))
                database_wrapper.save_database(users, messages, settings)

            # Get delivered messages command
            elif words[1] == "get_delivered":
                # Format: 'get_delivered receiver num_messages'
                receiver = words[2]  # logged in user

                # Validate that number of messages is an integer
                if words[3].isdigit():
                    num_msg_view = int(words[3])
                else:
                    send_message(
                        sock,
                        command,
                        data,
                        "error Number of messages to view must be an integer",
                    )
                    return

                delivered_msgs = messages["delivered"]

                if len(delivered_msgs) == 0 and num_msg_view > 0:
                    send_message(sock, command, data, "error No delivered messages")
                    return

                to_deliver = []
                # Gather the requested number of messages for this user
                for ind, msg_obj in enumerate(delivered_msgs):
                    if num_msg_view == 0:
                        break

                    if msg_obj["receiver"] == receiver:
                        to_deliver.append(
                            f"{msg_obj['id']}_{msg_obj['sender']}_{msg_obj['message']}"
                        )

                        num_msg_view -= 1

                send_message(sock, command, data, ("messages " + "\0".join(to_deliver)))

            # Home page command (refresh unread count)
            elif words[1] == "refresh_home":
                username = words[2]
                num_messages = get_new_messages(username)
                send_message(sock, command, data, f"refresh_home {num_messages}")

            # Delete message command
            elif words[1] == "delete_msg":
                current_user = words[2]
                # Format is 'delete_msg current_user msgid1,msgid2,...'
                msgids_to_delete = set(words[3].split(","))

                # Filter out messages that match those IDs and belong to current_user
                messages["delivered"] = [
                    msg
                    for msg in messages["delivered"]
                    if not (
                        str(msg["id"]) in msgids_to_delete
                        and msg["receiver"] == current_user
                    )
                ]

                # Refresh user's home screen
                num_messages = get_new_messages(current_user)
                send_message(sock, command, data, f"refresh_home {num_messages}")
                database_wrapper.save_database(users, messages, settings)

            else:
                # No recognized command was found
                print(f"No valid command: {command}")
                data.outb = data.outb[len(command) :]


if __name__ == "__main__":
    # Load the user, message, and settings database at startup
    users, messages, settings = database_wrapper.load_database()

    HOST = settings["host"]
    PORT = settings["port"]

    # Create, bind, and listen on the server socket
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.bind((HOST, PORT))
    lsock.listen()
    print("Listening on", (HOST, PORT))
    lsock.setblocking(False)
    # Register the listening socket to accept new connections
    sel.register(lsock, selectors.EVENT_READ, data=None)
    try:
        while True:
            events = sel.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    # If key.data is None, it means it's the listening socket
                    accept_wrapper(key.fileobj)
                else:
                    # Otherwise, it's an existing client connection
                    service_connection(key, mask)
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")
        sel.close()
    finally:
        sel.close()
