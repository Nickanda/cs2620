import json
import socket
import threading


class InternalCommunicator:
    def __init__(
        self, vm_id, allowed_hosts: list[str], starting_port: int, max_ports: int
    ):
        self.id = vm_id

        self.connectable_ports = []
        for host in allowed_hosts:
            for i in range(max_ports):
                self.connectable_ports.append((host, starting_port + i))

        self.connected_servers = []

    def updateConnectedMachines(self):
        for addr in self.connectable_ports:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect(addr)

                for saved_addr, conn in self.connected_servers:
                    if saved_addr == addr:
                        break

                self.connected_servers.appned((addr, s))
            except Exception:
                for ind, (saved_addr, conn) in enumerate(self.connected_servers):
                    if saved_addr == addr:
                        del self.connected_servers[ind]

    def distributeUpdate(self, update):
        for _, sock in self.connected_servers:
            data_obj = {
                "version": 0,
                "command": "internal_update",
                "data": update,
            }
            sock.send(json.dumps(data_obj).encode("utf-8"))

    def handleConnection(self, conn):
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
                            else:
                                print(f"VM {self.id}: Error parsing message: {line}")
                        except Exception as e:
                            print(f"VM {self.id}: Error parsing message: {e}")
            except Exception:
                break
        conn.close()

    def startServer(self, host, port):
        """Starts a TCP server to listen for incoming connections and messages."""
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((host, port))
        server_sock.listen(5)
        server_sock.settimeout(1.0)
        while True:
            try:
                conn, addr = server_sock.accept()
                # Start a new thread to handle the connection.
                threading.Thread(
                    target=self.handle_connection, args=(conn,), daemon=True
                ).start()
            except socket.timeout:
                continue
            except Exception as e:
                print(f"VM {self.id}: Server error: {e}")
