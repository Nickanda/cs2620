import server
import argparse
import sys


def parse_args(args):
    """
    Parse command-line arguments for the distributed server.
    """
    parser = argparse.ArgumentParser(description="Distributed Server Configuration")
    parser.add_argument(
        "--num_servers", type=int, default=2, help="Number of servers to start."
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
        help="Comma-separated list of other servers.",
    )
    parser.add_argument(
        "--internal_other_ports",
        type=str,
        default="50000",
        help="Comma-separated list of other server ports.",
    )
    parser.add_argument(
        "--internal_max_ports",
        type=str,
        default="10",
        help="Comma-separated list of other server ports.",
    )
    return parser.parse_args(args)


def main():
    args = parse_args(sys.argv[1:])

    server_ports = [args.start_server_port + i for i in range(args.num_servers)]
    internal_ports = [args.start_internal_port + i for i in range(args.num_servers)]

    processes = []

    for i, port in enumerate(server_ports):
        # Start a server for each port
        ser = server.FaultTolerantServer(
            id=i,
            host=args.host,
            port=port,
            current_starting_port=internal_ports[i],
            internal_other_servers=args.internal_other_servers.split(","),
            internal_other_ports=list(map(int, args.internal_other_ports.split(","))),
            internal_max_ports=list(map(int, args.internal_max_ports.split(","))),
        )
        ser.start()
        processes.append(ser)

    try:
        for ser in processes:
            ser.join()  # Wait for each server to finish
    except KeyboardInterrupt:
        for ser in processes:
            ser.terminate()
        print("Servers stopped.")


if __name__ == "__main__":
    main()
