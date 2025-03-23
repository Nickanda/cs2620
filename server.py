import database_wrapper
import fnmatch
import internal_communications
import json
import multiprocessing
import selectors
import socket
import types


class FaultTolerantServer(multiprocessing.Process):
    def __init__(
        self,
        id,
        host,
        port,
        current_starting_port=60000,
        internal_other_servers=["localhost"],
        internal_other_ports=[60000],
        internal_max_ports=[10],
    ):
        super().__init__()

        self.id = id
        self.host = host
        self.port = port

        self.internal_communicator_args = {
            "vm": self,
            "vm_id": id,
            "allowed_hosts": internal_other_servers,
            "starting_ports": internal_other_ports,
            "max_ports": internal_max_ports,
            "current_host": host,
            "current_port": current_starting_port,
        }

        users, messages, settings = database_wrapper.load_database(id)
        self.database = {
            "users": users,
            "messages": messages,
            "settings": settings,
        }

        self.sel = None

    def send_message(
        self, sock: socket.socket, data_length: int, command, data, message: str
    ):
        """
        Send a message back to the client. The message is a string, typically
        prefixed with a short command name, followed by a JSON payload.
        """
        data_obj = {
            "version": 0,
            "command": command,
            "data": message,
        }
        sock.send(json.dumps(data_obj).encode("utf-8"))
        data.outb = data.outb[data_length:]

    def send_error(
        self, sock: socket.socket, data_length: int, data, error_message: str
    ):
        """
        Helper function to send an error message back to the client in JSON format.
        """
        error_obj = {
            "version": 0,
            "command": "error",
            "data": {"error": error_message},
        }
        sock.send(json.dumps(error_obj).encode("utf-8"))
        data.outb = data.outb[data_length:]

    def parse_json_data(self, sock: socket.socket, data):
        decoded_data = data.outb.decode("utf-8")
        json_data = json.loads(decoded_data)
        version = json_data["version"]
        command = json_data["command"]
        command_data = json_data["data"]
        data_length = len(decoded_data)

        if version != 0:
            self.send_error(sock, data_length, data, "Unsupported protocol version")

        return command, command_data, data, data_length

    def get_new_messages(self, username: str):
        """
        Return the number of undelivered messages for a specific user.
        """
        num_messages = 0
        for msg_obj in self.database["messages"]["undelivered"]:
            if msg_obj["receiver"] == username:
                num_messages += 1
        return num_messages

    def create_account(self, sock: socket.socket, unparsed_data, internal_change=False):
        _, command_data, data, data_length = self.parse_json_data(sock, unparsed_data)
        username = command_data["username"].strip()
        password = command_data["password"].strip()

        if internal_change:
            self.database["users"][username] = {
                "password": password,
                "logged_in": True,
                "addr": None,
            }
            database_wrapper.save_database(
                self.id,
                self.database["users"],
                self.database["messages"],
                self.database["settings"],
            )
            return

        if not username.isalnum():
            self.send_error(sock, data_length, data, "Username must be alphanumeric")
            return

        if username in self.database["users"]:
            self.send_error(sock, data_length, data, "Username already exists")
            return

        if password.strip() == "":
            self.send_error(sock, data_length, data, "Password cannot be empty")
            return

        # Create new user in the users dict
        self.database["users"][username] = {
            "password": password,
            "logged_in": True,
            "addr": f"{data.addr[0]}:{data.addr[1]}",
        }

        return_dict = {"username": username, "undeliv_messages": 0}

        # Send a response indicating successful login with 0 unread messages
        self.send_message(sock, data_length, "login", data, return_dict)
        database_wrapper.save_database(
            self.id,
            self.database["users"],
            self.database["messages"],
            self.database["settings"],
        )
        self.internal_communicator.distribute_update(
            {
                "command": "create",
                "data": {
                    "username": username,
                    "password": password,
                },
            }
        )

    def login(self, sock: socket.socket, unparsed_data, internal_change=False):
        _, command_data, data, data_length = self.parse_json_data(sock, unparsed_data)

        username = command_data["username"]
        password = command_data.get("password")

        if internal_change:
            addr = command_data.get("addr")

            self.database["users"][username]["logged_in"] = True
            self.database["users"][username]["addr"] = addr
            database_wrapper.save_database(
                self.id,
                self.database["users"],
                self.database["messages"],
                self.database["settings"],
            )
            return

        if username not in self.database["users"]:
            self.send_error(sock, data_length, data, "Username does not exist")
            return

        if self.database["users"][username]["logged_in"]:
            self.send_error(sock, data_length, data, "User already logged in")
            return

        if password != self.database["users"][username]["password"]:
            self.send_error(sock, data_length, data, "Incorrect password")
            return

        # Count undelivered messages
        num_messages = self.get_new_messages(username)

        # Mark as logged in
        self.database["users"][username]["logged_in"] = True
        self.database["users"][username]["addr"] = f"{data.addr[0]}:{data.addr[1]}"

        return_dict = {"username": username, "undeliv_messages": num_messages}

        self.send_message(sock, data_length, "login", data, return_dict)
        database_wrapper.save_database(
            self.id,
            self.database["users"],
            self.database["messages"],
            self.database["settings"],
        )
        self.internal_communicator.distribute_update(
            {
                "command": "login",
                "data": {
                    "username": username,
                    "password": password,
                    "addr": f"{data.addr[0]}:{data.addr[1]}",
                },
            }
        )

    def logout(self, sock: socket.socket, unparsed_data, internal_change=False):
        _, command_data, data, data_length = self.parse_json_data(sock, unparsed_data)

        username = command_data["username"]

        if internal_change:
            self.database["users"][username]["logged_in"] = False
            self.database["users"][username]["addr"] = None
            database_wrapper.save_database(
                self.id,
                self.database["users"],
                self.database["messages"],
                self.database["settings"],
            )
            return

        if username not in self.database["users"]:
            self.send_error(sock, data_length, data, "Username does not exist")
            return

        # Mark user as logged out
        self.database["users"][username]["logged_in"] = False
        self.database["users"][username]["addr"] = None

        self.send_message(sock, data_length, "logout", data, {})
        database_wrapper.save_database(
            self.id,
            self.database["users"],
            self.database["messages"],
            self.database["settings"],
        )
        self.internal_communicator.distribute_update(
            {
                "command": "logout",
                "data": {
                    "username": username,
                },
            }
        )

    def search_messages(self, sock: socket.socket, unparsed_data):
        _, command_data, data, data_length = self.parse_json_data(sock, unparsed_data)

        pattern = command_data["search"]
        matched_users = fnmatch.filter(self.database["users"].keys(), pattern)

        return_dict = {"user_list": matched_users}

        self.send_message(sock, data_length, "user_list", data, return_dict)

    def delete_account(self, sock: socket.socket, unparsed_data, internal_change=False):
        _, command_data, data, data_length = self.parse_json_data(sock, unparsed_data)
        acct = command_data["username"]

        if internal_change:
            if acct in self.database["users"]:
                del self.database["users"][acct]

                def del_acct_msgs(msg_obj_lst, acct):
                    msg_obj_lst[:] = [
                        msg_obj
                        for msg_obj in msg_obj_lst
                        if msg_obj["sender"] != acct and msg_obj["receiver"] != acct
                    ]

                del_acct_msgs(self.database["messages"]["delivered"], acct)
                del_acct_msgs(self.database["messages"]["undelivered"], acct)

                database_wrapper.save_database(
                    self.id,
                    self.database["users"],
                    self.database["messages"],
                    self.database["settings"],
                )
            return

        if acct not in self.database["users"]:
            self.send_error(sock, data_length, data, "Account does not exist")
            return

        # Remove user
        del self.database["users"][acct]

        # Also remove messages where this user is sender or receiver
        def del_acct_msgs(msg_obj_lst, acct):
            msg_obj_lst[:] = [
                msg_obj
                for msg_obj in msg_obj_lst
                if msg_obj["sender"] != acct and msg_obj["receiver"] != acct
            ]

        del_acct_msgs(self.database["messages"]["delivered"], acct)
        del_acct_msgs(self.database["messages"]["undelivered"], acct)

        self.send_message(sock, data_length, "logout", data, {})
        database_wrapper.save_database(
            self.id,
            self.database["users"],
            self.database["messages"],
            self.database["settings"],
        )
        self.internal_communicator.distribute_update(
            {
                "command": "delete_acct",
                "data": {
                    "username": acct,
                },
            }
        )

    def deliver_message(
        self, sock: socket.socket, unparsed_data, internal_change=False
    ):
        _, command_data, data, data_length = self.parse_json_data(sock, unparsed_data)

        sender = command_data["sender"]
        receiver = command_data["recipient"]
        message = command_data["message"]

        if internal_change:
            self.database["settings"]["counter"] += 1
            msg_obj = {
                "id": self.database["settings"]["counter"],
                "sender": sender,
                "receiver": receiver,
                "message": message,
            }

            if self.database["users"][receiver]["logged_in"]:
                self.database["messages"]["delivered"].append(msg_obj)
            else:
                self.database["messages"]["undelivered"].append(msg_obj)

            database_wrapper.save_database(
                self.id,
                self.database["users"],
                self.database["messages"],
                self.database["settings"],
            )
            return

        if receiver not in self.database["users"]:
            self.send_error(sock, data_length, data, "Receiver does not exist")
            return

        # Increment the message counter
        self.database["settings"]["counter"] += 1
        msg_obj = {
            "id": self.database["settings"]["counter"],
            "sender": sender,
            "receiver": receiver,
            "message": message,
        }

        # Decide if message is delivered or undelivered based on receiver log-in status
        if self.database["users"][receiver]["logged_in"]:
            self.database["messages"]["delivered"].append(msg_obj)
        else:
            self.database["messages"]["undelivered"].append(msg_obj)

        # Return the new count of undelivered messages for the sender
        num_messages = self.get_new_messages(sender)
        return_dict = {"undeliv_messages": num_messages}

        self.send_message(sock, data_length, "refresh_home", data, return_dict)
        database_wrapper.save_database(
            self.id,
            self.database["users"],
            self.database["messages"],
            self.database["settings"],
        )
        self.internal_communicator.distribute_update(
            {
                "command": "send_msg",
                "data": {
                    "sender": sender,
                    "recipient": receiver,
                    "message": message,
                },
            }
        )

    def get_undelivered_messages(self, sock: socket.socket, unparsed_data):
        _, command_data, data, data_length = self.parse_json_data(sock, unparsed_data)

        # user decides on the number of messages to view
        receiver = command_data["username"]  # i.e. logged in user
        num_msg_view = command_data["num_messages"]

        delivered_msgs = self.database["messages"]["delivered"]
        undelivered_msgs = self.database["messages"]["undelivered"]

        to_deliver = []
        remove_indices = []  # List to store indices to delete later

        if len(undelivered_msgs) == 0 and num_msg_view > 0:
            self.send_error(sock, data_length, data, "No undelivered messages")
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
                remove_indices.append(ind)  # Store index instead of deleting in-place
                num_msg_view -= 1

        # Delete from undelivered_msgs in reverse order to avoid index shifting
        for ind in sorted(remove_indices, reverse=True):
            del undelivered_msgs[ind]

        return_dict = {"messages": to_deliver}

        self.send_message(sock, data_length, "messages", data, return_dict)
        database_wrapper.save_database(
            self.id,
            self.database["users"],
            self.database["messages"],
            self.database["settings"],
        )
        self.internal_communicator.distribute_update(
            {
                "command": "get_undelivered",
                "data": {
                    "username": receiver,
                    "num_messages": num_msg_view,
                },
            }
        )

    def get_delivered_messages(self, sock: socket.socket, unparsed_data):
        _, command_data, data, data_length = self.parse_json_data(sock, unparsed_data)

        # User decides on the number of messages to view
        receiver = command_data["username"]  # i.e. logged in user
        num_msg_view = command_data["num_messages"]

        delivered_msgs = self.database["messages"]["delivered"]

        if len(delivered_msgs) == 0 and num_msg_view > 0:
            self.send_error(sock, data_length, data, "No delivered messages")
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

        self.send_message(sock, data_length, "messages", data, return_dict)

    def refresh_home(self, sock: socket.socket, unparsed_data):
        _, command_data, data, data_length = self.parse_json_data(sock, unparsed_data)

        # Count up undelivered messages
        username = command_data["username"]

        num_messages = self.get_new_messages(username)

        return_dict = {"undeliv_messages": num_messages}

        self.send_message(sock, data_length, "refresh_home", data, return_dict)

    def delete_messages(
        self, sock: socket.socket, unparsed_data, internal_change=False
    ):
        _, command_data, data, data_length = self.parse_json_data(sock, unparsed_data)

        current_user = command_data["current_user"]
        msgids_to_delete = set(command_data["delete_ids"].split(","))

        if internal_change:
            self.database["messages"]["delivered"] = [
                msg
                for msg in self.database["messages"]["delivered"]
                if not (
                    str(msg["id"]) in msgids_to_delete
                    and msg["receiver"] == current_user
                )
            ]

            database_wrapper.save_database(
                self.id,
                self.database["users"],
                self.database["messages"],
                self.database["settings"],
            )
            return

        self.database["messages"]["delivered"] = [
            msg
            for msg in self.database["messages"]["delivered"]
            if not (
                str(msg["id"]) in msgids_to_delete and msg["receiver"] == current_user
            )
        ]

        num_messages = self.get_new_messages(current_user)

        return_dict = {"undeliv_messages": num_messages}

        self.send_message(sock, data_length, "refresh_home", data, return_dict)
        database_wrapper.save_database(
            self.id,
            self.database["users"],
            self.database["messages"],
            self.database["settings"],
        )
        self.internal_communicator.distribute_update(
            {
                "command": "delete_msg",
                "data": {
                    "current_user": current_user,
                    "delete_ids": ",".join(list(msgids_to_delete)),
                },
            }
        )

    def accept_wrapper(self, sock):
        """
        Accept a new socket connection and register it with the selector.
        """
        conn, addr = sock.accept()
        print(f"Accepted connection from {addr}")
        conn.setblocking(False)
        data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(conn, events, data=data)

    def service_connection(self, key, mask):
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
                self.sel.unregister(sock)
                sock.close()

                # Mark the corresponding user as logged out
                for user in self.database["users"]:
                    if (
                        self.database["users"][user]["addr"]
                        == f"{data.addr[0]}:{data.addr[1]}"
                    ):
                        self.database["users"][user]["logged_in"] = False
                        self.database["users"][user]["addr"] = None
                        self.internal_communicator.distribute_update(
                            {
                                "command": "logout",
                                "data": {
                                    "username": user,
                                },
                            }
                        )
                        break

                database_wrapper.save_database(
                    self.id,
                    self.database["users"],
                    self.database["messages"],
                    self.database["settings"],
                )
        if mask & selectors.EVENT_WRITE:
            if data.outb:
                # Decode the entire payload, split by space for the command,
                # then parse the rest as JSON
                received_data = data.outb.decode("utf-8")
                command, _, _, _ = self.parse_json_data(sock, data)

                ###################################################################
                # Process recognized JSON-based commands.
                ###################################################################

                if command == "create":
                    self.create_account(sock, data)
                elif command == "login":
                    self.login(sock, data)
                elif command == "logout":
                    self.logout(sock, data)
                elif command == "search":
                    self.search_messages(sock, data)
                elif command == "delete_acct":
                    self.delete_account(sock, data)
                elif command == "send_msg":
                    self.deliver_message(sock, data)
                elif command == "get_undelivered":
                    self.get_undelivered_messages(sock, data)
                elif command == "get_delivered":
                    self.get_delivered_messages(sock, data)
                elif command == "refresh_home":
                    self.refresh_home(sock, data)
                elif command == "delete_msg":
                    self.delete_messages(sock, data)
                else:
                    # Command not recognized
                    print(f"No valid command: {received_data}")
                    data.outb = data.outb[len(received_data) :]

    def run(self):
        self.sel = selectors.DefaultSelector()

        self.internal_communicator = internal_communications.InternalCommunicator(
            **self.internal_communicator_args
        )
        self.internal_communicator.start()

        # Create and bind the listening socket
        lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lsock.bind((self.host, self.port))
        lsock.listen()
        print("Listening on", (self.host, self.port))
        lsock.setblocking(False)
        self.sel.register(lsock, selectors.EVENT_READ, data=None)
        try:
            while True:
                events = self.sel.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        # Accept new connections
                        self.accept_wrapper(key.fileobj)
                    else:
                        # Service existing connections
                        self.service_connection(key, mask)
        except KeyboardInterrupt:
            print(f"{self.id} : Caught keyboard interrupt, exiting")
        finally:
            # self.on_exit()
            self.sel.close()
