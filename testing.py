import socket

import screens.signup

HOST = "127.0.0.1"
PORT = 54400

logged_in_user = None

def connect_socket():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        screens.signup.launch_window(s)
        while True:
            data = s.recv(4096)
            words = data.decode("utf-8").split()

            if words[0] == "login":
                logged_in_user = words[1]
                print(f"Logged in as {logged_in_user}")
            elif words[0] == "error":
                print(f"Error: {' '.join(words[1:])}")
                
            else: 
                command = " ".join(words)
                print(f"No valid command: {command}")

            print(f"Received: {data}")

if __name__ == "__main__":
    connect_socket()