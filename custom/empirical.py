import time
import socket
import database_wrapper

def measure_socket_command(command: str, host: str, port: int, iterations: int = 10):
    """
    For a given text command, this function:
      - Encodes the command (UTF-8) and measures its size in bytes.
      - Connects to the server, sends the command, and measures the round-trip latency.
    
    A new socket connection is established for each iteration so that each test is isolated.
    """
    # Encode the command and get its size in bytes.
    command_bytes = command.encode("utf-8")
    size_bytes = len(command_bytes)

    total_time = 0.0

    for _ in range(iterations):
        # Create a new socket connection for each iteration.
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            # Record the start time.
            start_time = time.time()
            # Send the entire command.
            s.sendall(command_bytes)
            # Wait for a response (assumed to be <=1024 bytes).
            _ = s.recv(1024)
            end_time = time.time()
            total_time += (end_time - start_time)

    avg_time = total_time / iterations
    return size_bytes, avg_time

def main():
    # Load client settings (host and port) from the client database.
    settings = database_wrapper.load_client_database()
    host = settings["host"]
    port = settings["port"]

    # Define a dictionary mapping command names to sample command strings.
    # Each command string starts with "0" (API version) followed by the command.
    # Note: These are sample commands; in a real test you might adjust the parameters
    # or use unique usernames to avoid conflicts.
    commands = {
        "CreateAccount": "0 create testuser password123",
        "Login": "0 login testuser password123",
        "Logout": "0 logout testuser",
        "Search": "0 search *",
        "DeleteAccount": "0 delete_acct testuser",
        "SendMessage": "0 send_msg testuser otheruser Hello, world!",
        "GetUndelivered": "0 get_undelivered testuser 5",
        "GetDelivered": "0 get_delivered testuser 5",
        "RefreshHome": "0 refresh_home testuser",
        "DeleteMessage": "0 delete_msg testuser 1,2,3",
    }

    iterations = 10  # Number of iterations for each command

    print("Empirical Data Collection for Socket-based Commands:\n")
    for cmd_name, cmd_str in commands.items():
        size_bytes, avg_time = measure_socket_command(cmd_str, host, port, iterations)
        print(f"{cmd_name}:")
        print(f"  Command string: '{cmd_str}'")
        print(f"  Serialized size: {size_bytes} bytes")
        print(f"  Avg round-trip time over {iterations} iterations: {avg_time * 1000:.2f} ms\n")

if __name__ == "__main__":
    main()
