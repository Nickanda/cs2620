import time
import grpc
import chat_pb2
import chat_pb2_grpc
import database_wrapper

def measure_request_response(stub, method_name, request, iterations=10):
    """
    Serializes the request to get its size and then measures the average 
    round-trip time for the given RPC method over a number of iterations.
    """
    # Get the size of the serialized request
    serialized = request.SerializeToString()
    size_bytes = len(serialized)
    
    total_time = 0.0
    # Execute the RPC call several times to average the response time
    for _ in range(iterations):
        start_time = time.time()
        # Dynamically call the RPC method on the stub
        getattr(stub, method_name)(request)
        end_time = time.time()
        total_time += (end_time - start_time)
    avg_time = total_time / iterations
    return size_bytes, avg_time

def main():
    # Load client settings (host/port)
    settings = database_wrapper.load_client_database()
    host = settings["host"]
    port = settings["port"]

    # Establish a gRPC channel and stub
    channel = grpc.insecure_channel(f"{host}:{port}")
    stub = chat_pb2_grpc.ChatServiceStub(channel)
    
    iterations = 10  # Number of iterations for timing each RPC call

    # Dictionary mapping command names to sample request objects.
    # Note: You might need to adjust the sample values based on your test data.
    commands = {
        "CreateAccount": chat_pb2.CreateAccountRequest(username="testuser", password="password123"),
        "Login": chat_pb2.LoginRequest(username="testuser", password="password123"),
        "Logout": chat_pb2.LogoutRequest(username="testuser"),
        "SendMessage": chat_pb2.SendMessageRequest(sender="testuser", receiver="otheruser", message="Hello, world!"),
        "GetUndelivered": chat_pb2.GetUndeliveredRequest(username="testuser", num_messages=5),
        "GetDelivered": chat_pb2.GetDeliveredRequest(username="testuser", num_messages=5),
        "DeleteAccount": chat_pb2.DeleteAccountRequest(username="testuser"),
        "SearchUsers": chat_pb2.SearchUsersRequest(pattern="*"),
        "DeleteMessage": chat_pb2.DeleteMessageRequest(username="testuser", message_ids=[1, 2, 3]),
        "RefreshHome": chat_pb2.RefreshHomeRequest(username="testuser"),
    }

    print("Empirical data collection for gRPC commands:\n")
    for command, request in commands.items():
        size_bytes, avg_time = measure_request_response(stub, command, request, iterations)
        print(f"{command}:\n"
              f"  Serialized size: {size_bytes} bytes\n"
              f"  Avg response time over {iterations} iterations: {avg_time * 1000:.2f} ms\n")

if __name__ == "__main__":
    main()
