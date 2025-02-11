import socket
import selectors
import types
import database_wrapper
import fnmatch

sel = selectors.DefaultSelector()

HOST = "127.0.0.1"
PORT = 54400

# 1: Creating an account. The user supplies a unique (login) name. If there is already an account with that name, the user is prompted for the password. If the name is not being used, the user is prompted to supply a password. The password should not be passed as plaintext.

# 2: Log in to an account. Using a login name and password, log into an account. An incorrect login or bad user name should display an error. A successful login should display the number of unread messages.

# 3: List accounts, or a subset of accounts that fit a text wildcard pattern. If there are more accounts than can comfortably be displayed, allow iterating through the accounts.

# 4. Send a message to a recipient. If the recipient is logged in, deliver immediately; if not the message should be stored until the recipient logs in and requests to see the message.

# 5: Read messages. If there are undelivered messages, display those messages. The user should be able to specify the number of messages they want delivered at any single time.

# 6. Delete a message or set of messages. Once deleted messages are gone.

# 7. Delete an account. You will need to specify the semantics of deleting an account that contains unread messages.

# ------------------------------------------------------------------------------

users = None
messages = None
settings = None

def accept_wrapper(sock):
    conn, addr = sock.accept()
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)

def send_message(sock: socket.socket, command: str, data, message: str):
    sock.send(message.encode("utf-8"))
    data.outb = data.outb[len(command):]

def get_new_messages(username):
    num_messages = 0
    for msg_obj in messages["undelivered"]:
        if msg_obj["receiver"] == username:
            num_messages += 1
    return num_messages

def service_connection(key, mask):
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
            print(f"Closing connection to {data.addr}")
            sel.unregister(sock)
            sock.close()

            for user in users:
                if users[user]["addr"] == data.addr[1]:
                    users[user]["logged_in"] = False
                    users[user]["addr"] = 0
                    break
            
            database_wrapper.save_database(users, messages, settings)
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            words = data.outb.decode("utf-8").split(" ")
            command = " ".join(words)
            if words[0] == "create":
                username = words[1]
                username.strip()
                password = " ".join(words[2:])

                if username.isalnum() == False:
                    send_message(sock, command, data, "error Username must be alphanumeric")
                    return

                if username in users:
                    send_message(sock, command, data, "error Username already exists")
                    return
                
                if password.strip() == "":
                    send_message(sock, command, data, "error Password cannot be empty")
                    return

                users[username] = {
                    "password": password,
                    "logged_in": True,
                    "addr": data.addr[1]
                }

                send_message(sock, command, data, f"login {username} 0")
                database_wrapper.save_database(users, messages, settings)

            elif words[0] == "login":
                username = words[1]
                password = " ".join(words[2:]).strip()

                if username not in users:
                    send_message(sock, command, data, "error Username does not exist")
                    return
                
                if users[username]["logged_in"]:
                    send_message(sock, command, data, "error User already logged in")
                    return
                
                if password != users[username]["password"]:
                    send_message(sock, command, data, "error Incorrect password")
                    return
                
                num_messages = 0
                for msg_obj in messages["undelivered"]:
                    if msg_obj["receiver"] == username:
                        num_messages += 1

                users[username]["logged_in"] = True
                users[username]["addr"] = data.addr[1]

                send_message(sock, command, data, f"login {username} {num_messages}")
                database_wrapper.save_database(users, messages, settings)

            elif words[0] == "logout":
                username = words[1]

                if username not in users:
                    send_message(sock, command, data, "error Username does not exist")
                    return
                
                users[username]["logged_in"] = False
                users[username]["addr"] = 0
    
                send_message(sock, command, data, "logout")
                database_wrapper.save_database(users, messages, settings)

            elif words[0] == "search":
                pattern = words[1] if len(words) > 1 else "*"
                matched_users = fnmatch.filter(users.keys(), pattern)

                send_message(sock, command, data, f"user_list {' '.join(matched_users)}") 
            
            elif words[0] == "delete_acct": 
                acct = words[1]
                
                # First, delete account from `users`
                if acct not in users:
                    send_message(sock, command, data, "error Account does not exist")
                    return

                del users[acct]

                # When deleting an account, delete all messages where the user is sender or receiver
                def del_acct_msgs(msg_obj_lst, acct):
                    msg_obj_lst[:] = [msg_obj for msg_obj in msg_obj_lst if msg_obj["sender"] != acct and msg_obj["receiver"] != acct]

                del_acct_msgs(messages["delivered"], acct)
                del_acct_msgs(messages["undelivered"], acct)

                send_message(sock, command, data, "logout")
                database_wrapper.save_database(users, messages, settings)

            elif words[0] == "send_msg":
                #! assumptions about the thing
                sender = words[1]
                receiver = words[2]
                message = ' '.join(words[3:])

                # if message is sent to a user that does not exist, raise an error
                if receiver not in users: 
                    send_message(sock, command, data, "error Receiver does not exist")
                    return 
                
                message = message.replace("\0", "NULL")

                settings["counter"] += 1
                msg_obj = {"id": settings["counter"],
                           "sender": sender, 
                           "receiver": receiver, 
                           "message": message}
                
                # if message is sent to a logged in user, mark it as delivered
                if users[receiver]["logged_in"]: 
                    messages["delivered"].append(msg_obj)
                # if message is sent to a user that is logged out, mark it as undelivered
                else: 
                    messages["undelivered"].append(msg_obj)

                num_messages = get_new_messages(sender)

                send_message(sock, command, data, f"refresh_home {num_messages}")
                database_wrapper.save_database(users, messages, settings)
            
            elif words[0] == "get_undelivered": 
                # user decides on the number of messages to view
                receiver = words[1]  # i.e. logged in user

                if words[2].isdigit():  # Ensures all characters are digits
                    num_msg_view = int(words[2])
                else:
                    send_message(sock, command, data, "error Number of messages to view must be an integer")
                    return

                num_msg_view = int(words[2])

                delivered_msgs = messages["delivered"]
                undelivered_msgs = messages["undelivered"]
                
                to_deliver = []
                remove_indices = []  # List to store indices to delete later

                if len(undelivered_msgs) == 0 and num_msg_view > 0: 
                    send_message(sock, command, data, "error No undelivered messages")
                    return
                
                for ind, msg_obj in enumerate(undelivered_msgs): 
                    if num_msg_view == 0: 
                        break 

                    if msg_obj["receiver"] == receiver: 
                        to_deliver.append(f'{msg_obj["id"]}_{msg_obj["sender"]}_{msg_obj["message"]}')
                        delivered_msgs.append(msg_obj)
                        remove_indices.append(ind)  # Store index instead of deleting in-place
                        num_msg_view -= 1
                
                # Delete from undelivered_msgs in reverse order to avoid index shifting
                for ind in sorted(remove_indices, reverse=True):
                    del undelivered_msgs[ind]

                send_message(sock, command, data, ("messages " + '\0'.join(to_deliver)))
                database_wrapper.save_database(users, messages, settings)
            
            elif words[0] == "get_delivered":
                # user decides on the number of messages to view
                receiver = words[1] # i.e. logged in user

                if words[2].isdigit():  # Ensures all characters are digits
                    num_msg_view = int(words[2])
                else:
                    send_message(sock, command, data, "error Number of messages to view must be an integer")
                    return
                # num_msg_view = int(words[2])
                
                delivered_msgs = messages["delivered"]
                undelivered_msgs = messages["undelivered"]
                
                if len(delivered_msgs) == 0 and num_msg_view > 0: 
                    send_message(sock, command, data, "error No delivered messages")
                    return
                
                to_deliver = []
                for ind, msg_obj in enumerate(delivered_msgs): 
                    if num_msg_view == 0: 
                        break 

                    if msg_obj["receiver"] == receiver: 
                        to_deliver.append(f'{msg_obj["id"]}_{msg_obj["sender"]}_{msg_obj["message"]}')

                        num_msg_view -= 1
                
                send_message(sock, command, data, ("messages " + '\0'.join(to_deliver)))
            
            elif words[0] == "refresh_home":
                # Count up undelivered messages
                username = words[1]

                num_messages = get_new_messages(username)

                send_message(sock, command, data, f"refresh_home {num_messages}")
            
            elif words[0] == "delete_msg":
                current_user = words[1]
                msgids_to_delete = set(words[2].split(","))
                messages["delivered"] = [msg for msg in messages["delivered"] 
                                         if not (str(msg["id"]) in msgids_to_delete 
                                         and msg["receiver"] == current_user)]
                
                num_messages = get_new_messages(current_user)

                send_message(sock, command, data, f"refresh_home {num_messages}")
                database_wrapper.save_database(users, messages, settings)

            else:
                print(f"No valid command: {command}")
                data.outb = data.outb[len(command):]

if __name__ == "__main__":
    users, messages, settings = database_wrapper.load_database()

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
                    accept_wrapper(key.fileobj)
                else:
                    service_connection(key, mask)
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")
        sel.close()
    finally:
        sel.close()
