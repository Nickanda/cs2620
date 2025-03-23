import server
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start distributed servers.")
    parser.add_argument(
        "--num_servers", type=int, default=5, help="Number of servers to start."
    )
    args = parser.parse_args()

    server_ports = [50000 + i for i in range(args.num_servers)]
    internal_ports = [60000 + i for i in range(args.num_servers)]

    for i, port in enumerate(server_ports):
        # Start a server for each port
        sys = server.FaultTolerantServer(
            i, "localhost", port, 60000, 10, internal_ports[i]
        )
        sys.start()
