import server
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start distributed servers.")
    parser.add_argument(
        "--num_servers", type=int, default=5, help="Number of servers to start."
    )
    parser.add_argument(
        "--start_server_port", type=int, default=50000, help="Starting server port."
    )
    parser.add_argument(
        "--start_internal_port", type=int, default=60000, help="Starting internal port."
    )
    parser.add_argument(
        "--host", type=str, default="localhost", help="Host for the servers."
    )
    parser.add_argument(
        "--internal_other_servers",
        type=str,
        default="localhost",
        help="Host for internal communication with other servers.",
    )
    parser.add_argument(
        "--internal_other_ports",
        type=str,
        default="60000",
        help="Comma-separated list of internal ports for other servers.",
    )
    parser.add_argument(
        "--internal_max_ports",
        type=str,
        default="10",
        help="Maximum number of ports for internal communication.",
    )
    args = parser.parse_args()

    server_ports = [args.start_server_port + i for i in range(args.num_servers)]
    internal_ports = [args.start_internal_port + i for i in range(args.num_servers)]

    processes = []

    for i, port in enumerate(server_ports):
        # Start a server for each port
        sys = server.FaultTolerantServer(
            id=i,
            host=args.host,
            port=port,
            current_starting_port=internal_ports[i],
            internal_other_servers=args.internal_other_servers.split(","),
            internal_other_ports=list(map(int, args.internal_other_ports.split(","))),
            internal_max_ports=list(map(int, args.internal_max_ports.split(","))),
        )
        sys.start()
        processes.append(sys)

    try:
        for sys in processes:
            sys.join()  # Wait for each server to finish
    except KeyboardInterrupt:
        for sys in processes:
            sys.terminate()
        print("Servers stopped.")
