"""
Client-side application for connecting to a server using a socket.

This script establishes a connection to a server at a specified host and port, handling
user authentication, navigation between different screens, and processing commands received
from the server.

Key Features:
- Uses JSON-based communication with the server instead of plain text commands.
- Supports user authentication (signup, login).
- Manages different UI states: home, messages, user list.
- Receives server responses as JSON objects, allowing structured data handling.
- Handles errors and displays messages using Tkinter's messagebox.

Last Updated: February 12, 2025
"""

import socket
from tkinter import messagebox
import screens_json.login
import screens_json.signup
import screens_json.home
import screens_json.messages
import screens_json.user_list
import json
import argparse
import time
import threading


def parse_arguments():
    """
    Parse command-line arguments for hosts, starting ports, and number of ports to test.
    """
    parser = argparse.ArgumentParser(
        description="Client-side application for connecting to a server."
    )
    parser.add_argument(
        "--hosts",
        type=str,
        default="localhost",
        help="Comma-separated list of hosts (default: localhost)",
    )
    parser.add_argument(
        "--ports",
        type=str,
        default="50000",
        help="Comma-separated list of starting port values (default: 50000)",
    )
    parser.add_argument(
        "--num_ports",
        type=str,
        default="10",
        help="Comma-separated list of number of ports to test (default: 10)",
    )
    return parser.parse_args()


connected_servers = []


def update_socket_thread(hosts, ports, num_ports):
    """
    Establishes a connection to the server by iterating over hosts and ports.
    """

    global connected_servers
    connectable_ports = []
    for i, host in enumerate(hosts):
        for port in ports:
            for counter in range(num_ports[i]):
                connectable_ports.append((host, port + counter))

    while True:
        connected_addrs = []

        for addr, conn in connected_servers:
            try:
                conn.sendall(
                    f"{json.dumps({'version': 0, 'command': 'check_connection', 'data': {}})}\0".encode(
                        "utf-8"
                    )
                )
                connected_addrs.append(addr)
            except Exception:
                print(f"CLIENT: Connection to {addr} lost.")
                conn.close()
                connected_servers.remove((addr, conn))

        for addr in connectable_ports:
            if addr in connected_addrs:
                continue

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect(addr)

                found_addr = False
                for saved_addr, _ in connected_servers:
                    if saved_addr == addr:
                        found_addr = True
                        break

                if not found_addr:
                    connected_servers.append((addr, s))
            except Exception:
                for ind, (saved_addr, conn) in enumerate(connected_servers):
                    if saved_addr == addr:
                        conn.close()
                        del connected_servers[ind]

        time.sleep(0.1)


def get_socket():
    """
    Establishes a connection to the server by iterating over hosts and ports.
    """
    global connected_servers
    if len(connected_servers) == 0:
        return None

    s = connected_servers[0][1]
    return s


def connect_socket(hosts, ports, num_ports):
    """
    Establishes a connection to the server and handles different UI states based on server responses.
    """
    logged_in_user = None
    current_state = "signup"  # Set initial state
    state_data = None

    # Iterate over hosts and ports to establish a connection
    try:
        # Create a socket and connect to the server
        while True:
            s = get_socket
            # Launch the appropriate UI screen based on the current state
            if current_state == "signup":
                screens_json.signup.launch_window(s)
            elif current_state == "login":
                screens_json.login.launch_window(s)
            elif current_state == "home" and logged_in_user is not None:
                screens_json.home.launch_window(s, logged_in_user, state_data)
            elif current_state == "messages" and logged_in_user is not None:
                screens_json.messages.launch_window(
                    s, state_data if state_data else [], logged_in_user
                )
            elif current_state == "user_list" and logged_in_user is not None:
                screens_json.user_list.launch_window(
                    s, state_data if state_data else "", logged_in_user
                )
            else:
                screens_json.signup.launch_window(
                    s,
                )  # Default to signup screen

            # Receive and decode data from the server
            s = get_socket()
            if s is None:
                print("Error: Could not connect to server!")
                messagebox.showerror("Error", "Could not connect to server!")
                break

            data = s.recv(1024)
            json_data = json.loads(data.decode("utf-8"))
            version = json_data["version"]
            command = json_data["command"]
            command_data = json_data["data"]

            # Handle different server commands
            if version != 0:
                print("Error: mismatch of API version!")
                messagebox.showerror("Error", "Mismatch of API version!")
            elif command == "login":
                # Store the logged-in username/undelivered messages and go to home
                logged_in_user = command_data["username"]
                state_data = command_data["undeliv_messages"]
                current_state = "home"
                print(f"Logged in as {logged_in_user}")
            elif command == "user_list":
                # Transition to the user list screen
                current_state = "user_list"
                state_data = command_data["user_list"]
            elif command == "error":
                # Handle errors from the server
                print(f"Error: {command_data['error']}")
                messagebox.showerror("Error", command_data["error"])
            elif command == "refresh_home":
                # Refresh the home screen with undelivered messages
                state_data = command_data["undeliv_messages"]
                current_state = "home"
            elif command == "messages":
                # Transition to the messages screen
                state_data = command_data["messages"]
                current_state = "messages"
            elif command == "logout":
                # Log out the user and go back to the signup screen
                logged_in_user = None
                current_state = "signup"
            else:
                # Handle unknown commands
                print(f"No valid command: {json_data}")
    except Exception as e:
        print(e)
        print("Error: Connection to server lost!")
        messagebox.showerror("Error", "Connection to server lost!")


# Run the socket connection when the script is executed
if __name__ == "__main__":
    args = parse_arguments()

    # Parse the comma-separated arguments into lists
    hosts = args.hosts.split(",")
    ports = list(map(int, args.ports.split(",")))
    num_ports = list(map(int, args.num_ports.split(",")))

    threading.Thread(
        target=update_socket_thread, args=(hosts, ports, num_ports)
    ).start()

    connect_socket(hosts, ports, num_ports)
