import socket
import selectors
import types
import database_wrapper

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
# def login
#   
# def create_account
#
# 

users = None
messages = None

def accept_wrapper(sock):
    conn, addr = sock.accept()
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)

def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(4096)
        if recv_data:
            data.outb += recv_data
        else:
            print(f"Closing connection to {data.addr}")
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            words = data.outb.decode("utf-8").split()
            if words[0] == "create":
                username = words[1]
                password = " ".join(words[2:])

                if username.isalnum() == False:
                    return_data = "error Username must be alphanumeric".encode("utf-8")
                    return

                if username in users:
                    return_data = "error Username already exists".encode("utf-8")
                    return

                users[username] = {
                    "password": password
                }

                return_data = f"login {username}".encode("utf-8")
                database_wrapper.save_database(users, messages)

            elif words[0] == "login":
                username = words[1]
                password = " ".join(words[2:])

                if username not in users:
                    return_data = "error Username does not exist".encode("utf-8")
                    return

                if users[username]["password"] != password:
                    return_data = "error Incorrect password".encode("utf-8")
                    return

                return_data = f"login {username}".encode("utf-8")
                database_wrapper.save_database(users, messages)
            else:
                command = " ".join(words)
                print(f"No valid command: {command}")
                return_data = "error Unknown command".encode("utf-8")
            sent = sock.send(return_data)
            data.outb = data.outb[sent:]

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
    finally:
        sel.close()
