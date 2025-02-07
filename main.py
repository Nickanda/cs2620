import socket
import selectors
import types
import database_wrapper
import argon2
import fnmatch
import datetime

sel = selectors.DefaultSelector()
hasher = argon2.PasswordHasher()

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


def accept_wrapper(sock):
    conn, addr = sock.accept()
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"", addr=addr)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)

def send_message(sock: socket.socket, command: str, data, message: bytes):
    sock.send(message)
    data.outb = data.outb[len(command):]

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
                if users[user]["addr"] == data.addr:
                    users[user]["logged_in"] = False
                    break
            
            database_wrapper.save_database(users, messages)
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            words = data.outb.decode("utf-8").split(" ")
            command = " ".join(words)
            if words[0] == "create":
                username = words[1]
                password = " ".join(words[2:])

                if username.isalnum() == False:
                    send_message(sock, command, data, "error Username must be alphanumeric".encode("utf-8"))
                    return

                if username in users:
                    send_message(sock, command, data, "error Username already exists".encode("utf-8"))
                    return

                users[username] = {
                    "password": password,
                    "logged_in": True,
                    "port": data.addr
                }

                send_message(sock, command, data, f"login {username}".encode("utf-8"))
                database_wrapper.save_database(users, messages)

            elif words[0] == "login":
                username = words[1]
                password = " ".join(words[2:])

                if username not in users:
                    send_message(sock, command, data, "error Username does not exist".encode("utf-8"))
                    return

                try:
                    hasher.verify(users[username]["password"], password)
                except argon2.exceptions.VerifyMismatchError:
                    send_message(sock, command, data, "error Incorrect password".encode("utf-8"))
                    return

                send_message(sock, command, data, f"login {username}".encode("utf-8"))

            elif words[0] == "search":
                pattern = words[1] if len(words) > 1 else "*"
                matched_users = fnmatch.filter(users.keys(), pattern)
                response = f"user_list {' '.join(matched_users)}"

                send_message(sock, command, data, response.encode("utf-8")) 
            
            elif words[0] == "delete_acct": 
                acct = words[1]
                # first delete account from `users`
                del users[acct]
                
                # when deleting an account, delete all messages that a user is the sender or receiver of 
                def del_acct_msgs(msg_obj_lst, acct): 
                    for msg_obj in msg_obj_lst: 
                        if msg_obj["sender"] == acct or msg_obj["receiver"] == acct: 
                            msg_obj_lst.remove(msg_obj)
                    return msg_obj_lst

                messages["delivered"] = del_acct_msgs(messages["delivered"], acct)
                messages["undelivered"] = del_acct_msgs(messages["undelivered"], acct)
                
                send_message(sock, command, data, "account_deleted".encode())

            elif words[0] == "send_msg":
                #! assumptions about the thing
                sender = words[1]
                receiver = words[2]
                message = words[3]

                # if message is sent to a user that does not exist, raise an error
                if receiver not in users: 
                    send_message(sock, command, data, "error Receiver does not exist")
                    return 
                
                msg_obj = {"id": len(messages["delivered"]) + len(messages["undelivered"]) + 1,
                           "sender": sender, 
                           "receiver": receiver, 
                           "message": message,
                           "timestamp": datetime.datetime.now()}

                # if message is sent to a logged in user, mark it as delivered
                if users[receiver["logged_in"]]: 
                    messages["delivered"].append(msg_obj)
                # if message is sent to a user that is logged out, mark it as undelivered
                else: 
                    messages["undelivered"].append(msg_obj)

                send_message(sock, command, data, "message_sent".encode())
                return 
            
            elif words[0] == "view_msg": 
                # user decides on the number of messages to view
                receiver = words[1] # i.e. logged in user
                num_msg_view = words[2]
                
                to_view = []
                to_deliver = ""
                for msg_obj in messages["undelivered"]: 
                    if num_msg_view == 0: 
                        pass 
                        
                    if msg_obj["receiver"] == receiver: 
                        to_deliver += (msg_obj["msg"] + " \0 ")
                        messages["delivered"].append(msg_obj)
                        messages["undelivered"].delete(msg_obj)
                        to_view.append(msg_obj)

                        num_msg_view -= 1
                
                send_message(sock, command, data, to_deliver.join("\0").encode())
                return

            else:
                print(f"No valid command: {command}")
                data.outb = data.outb[len(command):]

if __name__ == "__main__":
    users, messages = database_wrapper.load_database()

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
