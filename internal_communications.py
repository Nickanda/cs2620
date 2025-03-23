import json
import socket
import threading
import time


class InternalCommunicator(threading.Thread):
    def __init__(
        self,
        vm_id,
        allowed_hosts: list[str],
        starting_port: int,
        max_ports: int,
        current_host: str,
        current_port: int,
    ):
        super().__init__()

        self.id = vm_id

        self.connectable_ports = []
        for host in allowed_hosts:
            for i in range(max_ports):
                self.connectable_ports.append((host, starting_port + i))

        self.connected_servers = []

        self.host = current_host
        self.port = current_port

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
            time.sleep(5)

    def distribute_update(self, update):
        for _, sock in self.connected_servers:
            data_obj = {
                "version": 0,
                "command": "internal_update",
                "data": update,
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

                            if msg["command"] == "update_database":
                                break
                            elif msg["command"] == "action":
                                break
                            elif msg["command"] == "ping":
                                break
                            else:
                                print(
                                    f"INTERNAL {self.id}: Error parsing message: {line}"
                                )
                        except Exception as e:
                            print(f"INTERNAL {self.id}: Error parsing message: {e}")
            except Exception:
                break
        conn.close()

    def run(self):
        """Starts a TCP server to listen for incoming connections and messages."""
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((self.host, self.port))
        print(f"INTERNAL {self.id}: Listening on {self.host}:{self.port}")
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
