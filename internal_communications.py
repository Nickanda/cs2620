import json
import socket
import threading
import time


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
            for counter in range(max_ports[i]):
                self.connectable_ports.append((host, starting_ports[i] + counter))

        self.connected_servers = []

        self.host = current_host
        self.port = current_port

        self.leader = None  # Store the current leader

    def update_connected_machines(self):
        while True:
            connected_addrs = []

            for addr, conn in self.connected_servers:
                try:
                    conn.sendall(
                        f"{json.dumps({'version': 0, 'command': 'ping'})}\n".encode(
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

            time.sleep(5)

    def check_and_elect_leader(self):
        if (
            not self.leader
            or self.leader
            not in [self.port] + [addr[1] for addr, _ in self.connected_servers]
            or self.leader
            < min([self.port] + [addr[1] for addr, _ in self.connected_servers])
        ):
            print(f"INTERNAL {self.id}: No leader detected. Initiating election.")
            self.elect_leader()

    def elect_leader(self):
        # Elect the leader as the VM with the smallest ID
        all_ids = [self.port] + [addr[1] for addr, _ in self.connected_servers]
        new_leader = min(all_ids)
        self.leader = new_leader
        print(f"INTERNAL {self.id}: New leader elected: {self.leader}")
        for _, sock in self.connected_servers:
            data_obj = {
                "version": 0,
                "command": "internal_update",
                "data": {"leader": self.leader},
            }
            sock.sendall(f"{json.dumps(data_obj)}\n".encode("utf-8"))

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
            sock.sendall(f"{json.dumps(data_obj)}\n".encode("utf-8"))

    def handle_connection(self, conn):
        """Handles an incoming connection, reading messages and enqueuing them."""
        buffer = ""
        while True:
            try:
                data = conn.recv(1024).decode("utf-8")
                if not data:
                    break
                buffer += data
                # Process complete messages terminated by newline.
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line:
                        try:
                            msg = json.loads(line)

                            if msg["command"] == "ping":
                                break
                            elif msg["command"] == "internal_update":
                                if "leader" in msg["data"]:
                                    self.leader = msg["data"]["leader"]
                                    print(
                                        f"INTERNAL {self.id}: Leader updated to {self.leader}"
                                    )
                            elif msg["command"] == "distribute_updae":
                                command = msg["data"]["command"]
                                received_data = msg["data"]

                                if command == "create":
                                    self.vm.create_account(conn, received_data, True)
                                elif command == "login":
                                    self.vm.login(conn, received_data, True)
                                elif command == "logout":
                                    self.vm.logout(conn, received_data, True)
                                elif command == "search":
                                    self.vm.search_messages(conn, received_data, True)
                                elif command == "delete_acct":
                                    self.vm.delete_account(conn, received_data, True)
                                elif command == "send_msg":
                                    self.vm.deliver_message(conn, received_data, True)
                                elif command == "get_undelivered":
                                    self.vm.get_undelivered_messages(
                                        conn, received_data, True
                                    )
                                elif command == "get_delivered":
                                    self.vm.get_delivered_messages(
                                        conn, received_data, True
                                    )
                                elif command == "refresh_home":
                                    self.vm.refresh_home(conn, received_data, True)
                                elif command == "delete_msg":
                                    self.vm.delete_messages(conn, received_data, True)
                                else:
                                    # Command not recognized
                                    print(f"No valid command: {received_data}")
                                    data.outb = data.outb[len(received_data) :]
                            elif msg["command"] == "get_database":
                                for addr, sock in self.connected_servers:
                                    if (
                                        addr[0] == msg["host"]
                                        and addr[1] == msg["port"]
                                    ):
                                        sock.sendall(
                                            f"{json.dumps({'version': 0, 'command': 'set_database_users', 'data': self.vm.database['users']})}\n".encode(
                                                "utf-8"
                                            )
                                        )
                                        sock.sendall(
                                            f"{json.dumps({'version': 0, 'command': 'set_database_messages', 'data': self.vm.database['messages']})}\n".encode(
                                                "utf-8"
                                            )
                                        )
                                        sock.sendall(
                                            f"{json.dumps({'version': 0, 'command': 'set_database_settings', 'data': self.vm.database['settings']})}\n".encode(
                                                "utf-8"
                                            )
                                        )
                            elif msg["command"] == "set_database_users":
                                self.vm.database["users"] = msg["data"]
                            elif msg["command"] == "set_database_messages":
                                self.vm.database["messages"] = msg["data"]
                            elif msg["command"] == "set_database_settings":
                                self.vm.database["settings"] = msg["data"]
                            else:
                                print(
                                    f"INTERNAL {self.id}: Error parsing message: {line}"
                                )
                        except Exception as e:
                            print(f"INTERNAL {self.id}: Error parsing message: {e}")
            except Exception:
                break
        conn.close()

    def get_database_from_leader(self):
        """Fetches the database from the current leader."""
        if self.leader:
            for addr, conn in self.connected_servers:
                if addr[1] == self.leader:
                    try:
                        conn.sendall(
                            f"{json.dumps({'version': 0, 'command': 'get_database', 'host': self.host, 'port': self.port})}\n".encode(
                                "utf-8"
                            )
                        )
                    except Exception as e:
                        print(f"INTERNAL {self.id}: Error fetching database: {e}")

    def run(self):
        """Starts a TCP server to listen for incoming connections and messages."""
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((self.host, self.port))
        server_sock.listen(5)
        server_sock.settimeout(1.0)
        threading.Thread(target=self.update_connected_machines, daemon=True).start()
        while True:
            try:
                conn, addr = server_sock.accept()
                self.handle_connection(conn)
            except socket.timeout:
                continue
            except Exception as e:
                print(f"INTERNAL {self.id}: Server error: {e}")
