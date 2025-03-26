import json
import socket
import threading
import time
import database_wrapper
import selectors
import types


class InternalCommunicator(threading.Thread):
    def __init__(
        self,
        vm,
        vm_id,
        allowed_hosts: list[str],
        starting_ports: list[int],
        max_ports: list[int],
        current_host: str,
        current_port: int,
    ):
        super().__init__()

        self.vm = vm
        self.id = vm_id

        self.connectable_ports = []
        for i, host in enumerate(allowed_hosts):
            for port in starting_ports:
                for counter in range(max_ports[i]):
                    self.connectable_ports.append((host, port + counter))

        self.connected_servers = []

        self.host = current_host
        self.port = current_port

        self.leader = None  # Store the current leader
        self.loaded_database = False

    def get_database_from_leader(self):
        """Fetches the database from the current leader."""
        if self.leader is not None:
            for addr, conn in self.connected_servers:
                if f"{addr[0]}:{addr[1]}" == self.leader:
                    try:
                        conn.sendall(
                            f"{json.dumps({'version': 0, 'command': 'get_database', 'host': self.host, 'port': self.port})}\0".encode(
                                "utf-8"
                            )
                        )
                    except Exception as e:
                        print(f"INTERNAL {self.id}: Error fetching database: {e}")

    def update_connected_machines(self):
        while True:
            connected_addrs = []

            for addr, conn in self.connected_servers:
                try:
                    conn.sendall(
                        f"{json.dumps({'version': 0, 'command': 'ping'})}\0".encode(
                            "utf-8"
                        )
                    )
                    connected_addrs.append(addr)
                except Exception:
                    print(f"INTERNAL {self.id}: Connection to {addr} lost.")
                    conn.close()
                    self.connected_servers.remove((addr, conn))

            for addr in self.connectable_ports:
                if addr in connected_addrs or addr == (self.host, self.port):
                    continue

                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    s.connect(addr)

                    found_addr = False
                    for saved_addr, _ in self.connected_servers:
                        if saved_addr == addr:
                            found_addr = True
                            break

                    if not found_addr:
                        self.connected_servers.append((addr, s))
                except Exception:
                    for ind, (saved_addr, conn) in enumerate(self.connected_servers):
                        if saved_addr == addr:
                            conn.close()
                            del self.connected_servers[ind]

            # Check and elect a leader if necessary
            self.check_and_elect_leader()

            if not self.loaded_database:
                self.get_database_from_leader()

            time.sleep(1)

    def check_and_elect_leader(self):
        if (
            not self.leader
            or self.leader
            not in [f"{self.host}:{self.port}"]
            + [f"{addr[0]}:{addr[1]}" for addr, _ in self.connected_servers]
            or self.leader
            < min(
                [f"{self.host}:{self.port}"]
                + [f"{addr[0]}:{addr[1]}" for addr, _ in self.connected_servers]
            )
        ):
            print(f"INTERNAL {self.id}: No leader detected. Initiating election.")
            self.elect_leader()

    def elect_leader(self):
        # Elect the leader as the VM with the smallest ID
        all_ids = [f"{self.host}:{self.port}"] + [
            f"{addr[0]}:{addr[1]}" for addr, _ in self.connected_servers
        ]
        new_leader = min(all_ids)
        self.leader = new_leader
        self.loaded_database = False
        print(f"INTERNAL {self.id}: New leader elected: {self.leader}")

    def distribute_update(self, update):
        for _, sock in self.connected_servers:
            data_obj = {
                "version": 0,
                "command": "distribute_update",
                "data": {
                    "version": 0,
                    "command": update["command"],
                    "data": update["data"],
                },
            }
            sock.sendall(f"{json.dumps(data_obj)}\0".encode("utf-8"))

    def handle_connection(self, key, mask):
        """Handles an incoming connection, reading messages and enqueuing them."""
        conn = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ:
            try:
                recv_data = conn.recv(4096)
            except ConnectionResetError:
                recv_data = None

            if recv_data:
                data.outb += recv_data
            else:
                self.sel.unregister(conn)
                conn.close()
                return
        if mask & selectors.EVENT_WRITE:
            if data.outb:
                # Process complete messages terminated by newline.

                lines = data.outb.decode("utf-8").split("\0")[:-1]
                for line in lines:
                    try:
                        msg = json.loads(line)

                        if msg["command"] == "ping":
                            pass
                        elif msg["command"] == "internal_update":
                            if "leader" in msg["data"]:
                                self.leader = msg["data"]["leader"]
                                print(
                                    f"INTERNAL {self.id}: Leader updated to {self.leader}"
                                )
                        elif msg["command"] == "distribute_update":
                            command = msg["data"]["command"]
                            received_data = msg["data"]

                            if command == "create":
                                self.vm.create_account(conn, received_data, True)
                            elif command == "login":
                                self.vm.login(conn, received_data, True)
                            elif command == "logout":
                                self.vm.logout(conn, received_data, True)
                            elif command == "search":
                                self.vm.search_messages(conn, received_data)
                            elif command == "delete_acct":
                                self.vm.delete_account(conn, received_data, True)
                            elif command == "send_msg":
                                self.vm.deliver_message(conn, received_data, True)
                            elif command == "get_undelivered":
                                self.vm.get_undelivered_messages(conn, received_data)
                            elif command == "get_delivered":
                                self.vm.get_delivered_messages(conn, received_data)
                            elif command == "refresh_home":
                                self.vm.refresh_home(conn, received_data)
                            elif command == "delete_msg":
                                self.vm.delete_messages(conn, received_data, True)
                            else:
                                # Command not recognized
                                print(f"No valid command: {received_data}")
                                data.outb = data.outb[len(received_data) :]
                        elif msg["command"] == "get_database":
                            for addr, sock in self.connected_servers:
                                if addr[0] == msg["host"] and addr[1] == msg["port"]:
                                    sock.sendall(
                                        (
                                            json.dumps(
                                                {
                                                    "version": 0,
                                                    "command": "set_database",
                                                    "data": {
                                                        "users": self.vm.database[
                                                            "users"
                                                        ],
                                                        "messages": self.vm.database[
                                                            "messages"
                                                        ],
                                                        "settings": self.vm.database[
                                                            "settings"
                                                        ],
                                                    },
                                                }
                                            )
                                            + "\0"
                                        ).encode("utf-8")
                                    )
                        elif msg["command"] == "set_database":
                            print(f"INTERNAL {self.id}: Updating users database")
                            self.vm.database["users"] = msg["data"]["users"]
                            print(f"INTERNAL {self.id}: Updating messages database")
                            self.vm.database["messages"] = msg["data"]["messages"]
                            print(f"INTERNAL {self.id}: Updating settings database")
                            self.vm.database["settings"] = msg["data"]["settings"]
                            database_wrapper.save_database(
                                self.id,
                                self.vm.database["users"],
                                self.vm.database["messages"],
                                self.vm.database["settings"],
                            )
                            print(f"INTERNAL {self.id}: Updating COMPLETE database")
                            self.loaded_database = True
                        else:
                            print(f"INTERNAL {self.id}: Error parsing message: {line}")
                    except Exception as e:
                        print(
                            f"INTERNAL {self.id}: Error parsing message: {e}\n\nLINE: {line}"
                        )

                data.outb = data.outb[len(data.outb.decode("utf-8")) :]

    def accept_wrapper(self, sock):
        """
        Accept a new socket connection and register it with the selector.
        """
        conn, addr = sock.accept()
        print(f"INTERNAL: Accepted connection from {addr}")
        conn.setblocking(False)
        data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(conn, events, data=data)

    def run(self):
        """Starts a TCP server to listen for incoming connections and messages."""
        self.sel = selectors.DefaultSelector()

        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((self.host, self.port))
        server_sock.listen()
        server_sock.setblocking(False)
        self.sel.register(server_sock, selectors.EVENT_READ, data=None)

        threading.Thread(target=self.update_connected_machines, daemon=True).start()

        while True:
            events = self.sel.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    self.accept_wrapper(key.fileobj)
                else:
                    self.handle_connection(key, mask)
