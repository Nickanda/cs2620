import chat_pb2

def simulate_message_serialization():
    # Create a sample SendMessageRequest and measure its serialized size.
    msg = chat_pb2.SendMessageRequest(sender="alice", receiver="bob", message="Hello Bob! This is a test message.")
    serialized = msg.SerializeToString()
    print("Serialized SendMessageRequest size:", len(serialized), "bytes")

def simulate_bulk_messages(n):
    # Create n Message objects and wrap them in a GetUndeliveredResponse.
    messages = []
    for i in range(n):
        msg = chat_pb2.Message(id=i+1, sender="alice", message=f"Test message {i+1}")
        messages.append(msg)
    response = chat_pb2.GetUndeliveredResponse(status="success", message="Bulk test", messages=messages)
    serialized = response.SerializeToString()
    print(f"Serialized GetUndeliveredResponse with {n} messages size:", len(serialized), "bytes")

if __name__ == "__main__":
    simulate_message_serialization()
    simulate_bulk_messages(50)
