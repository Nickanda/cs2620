import time
import socket
import json
import database_wrapper

def measure_json_command(command: str, host: str, port: int, iterations: int = 10):
    """
    For a given JSON-based command, this function:
      - Encodes the command (UTF-8) and measures its size in bytes.
      - Connects to the server, sends the command, and measures the round-trip latency.
    
    Each iteration establishes a new connection to ensure test isolation.
    """
    command_bytes = command.encode("utf-8")
    size_bytes = len(command_bytes)
    total_time = 0.0

    for _ in range(iterations):
        # Establish a new connection for each test iteration.
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            start_time = time.time()
            s.sendall(command_bytes)
            # Wait for a response (assumes response is ≤1024 bytes)
            _ = s.recv(1024)
            end_time = time.time()
            total_time += (end_time - start_time)
    
    avg_time = total_time / iterations
    return size_bytes, avg_time

def main():
    # Load client settings (using host_json and port_json for JSON-based protocol)
    settings = database_wrapper.load_client_database()
    host = settings["host_json"]
    port = settings["port_json"]

    # Define sample commands. Each command follows the protocol:
    # "0 <command> <json_payload>"
    commands = {
        "CreateAccount": "0 create " + json.dumps({"username": "testuser", "password": "password123"}),
        "Login":         "0 login " + json.dumps({"username": "testuser", "password": "password123"}),
        "Logout":        "0 logout " + json.dumps({"username": "testuser"}),
        "Search":        "0 search " + json.dumps({"pattern": "*"}),
        "DeleteAccount": "0 delete_acct " + json.dumps({"username": "testuser"}),
        "SendMessage":   "0 send_msg " + json.dumps({
                                "sender": "testuser",
                                "receiver": "otheruser",
                                "message": "Hello, world!"
                           }),
        "GetUndelivered": "0 get_undelivered " + json.dumps({
                                "username": "testuser",
                                "num_messages": 5
                           }),
        "GetDelivered":  "0 get_delivered " + json.dumps({
                                "username": "testuser",
                                "num_messages": 5
                           }),
        "RefreshHome":   "0 refresh_home " + json.dumps({"username": "testuser"}),
        "DeleteMessage": "0 delete_msg " + json.dumps({
                                "username": "testuser",
                                "message_ids": [1, 2, 3]
                           })
    }

    iterations = 10  # Number of iterations per command

    print("Empirical Data Collection for JSON-based Socket Commands:\n")
    for cmd_name, cmd_str in commands.items():
        size_bytes, avg_time = measure_json_command(cmd_str, host, port, iterations)
        print(f"{cmd_name}:")
        print(f"  Command string: '{cmd_str}'")
        print(f"  Serialized size: {size_bytes} bytes")
        print(f"  Avg round-trip time over {iterations} iterations: {avg_time * 1000:.2f} ms\n")

if __name__ == "__main__":
    main()
