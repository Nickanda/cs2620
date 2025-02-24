import grpc
import chat_pb2
import chat_pb2_grpc
import time
import json
import sys

def run_grpc_experiment(num_users, num_messages):
    channel = grpc.insecure_channel('localhost:50051')
    stub = chat_pb2_grpc.ChatServiceStub(channel)

    # Measure time and data size for user creation
    start_time = time.time()
    total_data_size = 0

    for i in range(num_users):
        username = f"user{i}"
        password = f"pass{i}"
        response = stub.CreateAccount(chat_pb2.CreateAccountRequest(username=username, password=password))
        total_data_size += sys.getsizeof(response)

    user_creation_time = time.time() - start_time

    # Measure time and data size for sending messages
    start_time = time.time()

    for i in range(num_messages):
        sender = f"user{i % num_users}"
        receiver = f"user{(i + 1) % num_users}"
        message = f"Message {i} from {sender} to {receiver}"
        response = stub.SendMessage(chat_pb2.SendMessageRequest(sender=sender, receiver=receiver, message=message))
        total_data_size += sys.getsizeof(response)

    message_sending_time = time.time() - start_time

    # Measure time and data size for retrieving messages
    start_time = time.time()

    for i in range(num_users):
        username = f"user{i}"
        response = stub.GetUndeliveredMessages(chat_pb2.GetMessagesRequest(username=username, max_messages=10))
        total_data_size += sys.getsizeof(response)

    message_retrieval_time = time.time() - start_time

    return {
        "user_creation_time": user_creation_time,
        "message_sending_time": message_sending_time,
        "message_retrieval_time": message_retrieval_time,
        "total_data_size": total_data_size
    }

def run_json_experiment(num_users, num_messages):
    # Simulate JSON-based operations
    start_time = time.time()
    total_data_size = 0

    for i in range(num_users):
        username = f"user{i}"
        password = f"pass{i}"
        data = json.dumps({"action": "create_account", "username": username, "password": password})
        total_data_size += sys.getsizeof(data)

    user_creation_time = time.time() - start_time

    start_time = time.time()

    for i in range(num_messages):
        sender = f"user{i % num_users}"
        receiver = f"user{(i + 1) % num_users}"
        message = f"Message {i} from {sender} to {receiver}"
        data = json.dumps({"action": "send_message", "sender": sender, "receiver": receiver, "message": message})
        total_data_size += sys.getsizeof(data)

    message_sending_time = time.time() - start_time

    start_time = time.time()

    for i in range(num_users):
        username = f"user{i}"
        data = json.dumps({"action": "get_undelivered_messages", "username": username, "max_messages": 10})
        total_data_size += sys.getsizeof(data)

    message_retrieval_time = time.time() - start_time

    return {
        "user_creation_time": user_creation_time,
        "message_sending_time": message_sending_time,
        "message_retrieval_time": message_retrieval_time,
        "total_data_size": total_data_size
    }

def main():
    num_users = 1000
    num_messages = 10000

    grpc_results = run_grpc_experiment(num_users, num_messages)
    json_results = run_json_experiment(num_users, num_messages)

    print("gRPC Results:")
    print(json.dumps(grpc_results, indent=2))
    print("\nJSON Results:")
    print(json.dumps(json_results, indent=2))

    print("\nComparison:")
    print(f"User Creation Time: gRPC is {json_results['user_creation_time'] / grpc_results['user_creation_time']:.2f}x faster")
    print(f"Message Sending Time: gRPC is {json_results['message_sending_time'] / grpc_results['message_sending_time']:.2f}x faster")
    print(f"Message Retrieval Time: gRPC is {json_results['message_retrieval_time'] / grpc_results['message_retrieval_time']:.2f}x faster")
    print(f"Total Data Size: gRPC uses {grpc_results['total_data_size'] / json_results['total_data_size']:.2f}x less data")

if __name__ == "__main__":
    main()