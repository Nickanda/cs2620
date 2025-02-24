import grpc
import chat_pb2
import chat_pb2_grpc
import database_wrapper

def run():
    settings = database_wrapper.load_client_database()
    channel = grpc.insecure_channel(f"{settings['host']}:{settings['port']}")
    stub = chat_pb2_grpc.ChatServiceStub(channel)

    # 1. Create account for "alice"
    print("Creating account 'alice'")
    response = stub.CreateAccount(chat_pb2.CreateAccountRequest(username="alice", password="alicepwd"))
    print("Response:", response.status, response.message)

    # 2. Login as "alice"
    print("Logging in as 'alice'")
    response = stub.Login(chat_pb2.LoginRequest(username="alice", password="alicepwd"))
    print("Response:", response.status, response.message, "Undelivered messages:", response.undelivered_count)

    # 3. Send a message from alice to bob (bob does not exist yet)
    print("Sending message from 'alice' to 'bob'")
    response = stub.SendMessage(chat_pb2.SendMessageRequest(sender="alice", receiver="bob", message="Hello Bob!"))
    print("Response:", response.status, response.message)

    # 4. Create account and login for "bob"
    print("Creating account 'bob'")
    response = stub.CreateAccount(chat_pb2.CreateAccountRequest(username="bob", password="bobpwd"))
    print("Response:", response.status, response.message)
    
    print("Logging in as 'bob'")
    response = stub.Login(chat_pb2.LoginRequest(username="bob", password="bobpwd"))
    print("Response:", response.status, response.message, "Undelivered messages:", response.undelivered_count)

    # 5. Get undelivered messages for bob
    print("Retrieving undelivered messages for 'bob'")
    response = stub.GetUndelivered(chat_pb2.GetUndeliveredRequest(username="bob", num_messages=10))
    print("Response:", response.status, response.message)
    for msg in response.messages:
        print(f"Message {msg.id} from {msg.sender}: {msg.message}")

    # 6. Search for users starting with 'a'
    print("Searching users with pattern 'a*'")
    response = stub.SearchUsers(chat_pb2.SearchUsersRequest(pattern="a*"))
    print("Response:", response.status, "Users:", response.users)

    # 7. Delete a message (for example, message with id 1 for bob)
    print("Deleting message id 1 for 'bob'")
    response = stub.DeleteMessage(chat_pb2.DeleteMessageRequest(username="bob", message_ids=[1]))
    print("Response:", response.status, response.message)

    # 8. Logout for both users
    print("Logging out 'alice'")
    response = stub.Logout(chat_pb2.LogoutRequest(username="alice"))
    print("Response:", response.status, response.message)

    print("Logging out 'bob'")
    response = stub.Logout(chat_pb2.LogoutRequest(username="bob"))
    print("Response:", response.status, response.message)

if __name__ == "__main__":
    run()
