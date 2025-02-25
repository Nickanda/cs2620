import grpc
from concurrent import futures
import time
import fnmatch

import chat_pb2
import chat_pb2_grpc
import database_wrapper

# Load the databases from JSON files.
users, messages, settings = database_wrapper.load_database()


def get_new_messages(username):
    count = 0
    for msg in messages["undelivered"]:
        if msg["receiver"] == username:
            count += 1
    return count


class ChatServiceServicer(chat_pb2_grpc.ChatServiceServicer):
    def CreateAccount(self, request, context):
        username = request.username.strip()
        password = request.password.strip()
        if not username.isalnum():
            return chat_pb2.CreateAccountResponse(
                status="error", message="Username must be alphanumeric"
            )
        if username in users:
            return chat_pb2.CreateAccountResponse(
                status="error", message="Username already exists"
            )
        if password == "":
            return chat_pb2.CreateAccountResponse(
                status="error", message="Password cannot be empty"
            )
        users[username] = {"password": password, "logged_in": True, "addr": 0}
        database_wrapper.save_database(users, messages, settings)
        return chat_pb2.CreateAccountResponse(
            status="success", message=f"Account created. Logged in as {username}."
        )

    def Login(self, request, context):
        username = request.username.strip()
        password = request.password.strip()
        if username not in users:
            return chat_pb2.LoginResponse(
                status="error", message="Username does not exist", undelivered_count=0
            )
        if users[username]["logged_in"]:
            return chat_pb2.LoginResponse(
                status="error", message="User already logged in", undelivered_count=0
            )
        if password != users[username]["password"]:
            return chat_pb2.LoginResponse(
                status="error", message="Incorrect password", undelivered_count=0
            )
        users[username]["logged_in"] = True
        undelivered_count = get_new_messages(username)
        database_wrapper.save_database(users, messages, settings)
        return chat_pb2.LoginResponse(
            status="success",
            message=f"Logged in as {username}.",
            undelivered_count=undelivered_count,
        )

    def Logout(self, request, context):
        username = request.username.strip()
        if username not in users:
            return chat_pb2.LogoutResponse(
                status="error", message="Username does not exist"
            )
        users[username]["logged_in"] = False
        users[username]["addr"] = 0
        database_wrapper.save_database(users, messages, settings)
        return chat_pb2.LogoutResponse(
            status="success", message="Logged out successfully."
        )

    def SendMessage(self, request, context):
        sender = request.sender.strip()
        receiver = request.receiver.strip()
        msg_text = request.message.strip()
        if receiver not in users:
            return chat_pb2.SendMessageResponse(
                status="error", message="Receiver does not exist"
            )
        settings["counter"] += 1
        msg_obj = {
            "id": settings["counter"],
            "sender": sender,
            "receiver": receiver,
            "message": msg_text,
        }
        if users[receiver]["logged_in"]:
            messages["delivered"].append(msg_obj)
        else:
            messages["undelivered"].append(msg_obj)
        database_wrapper.save_database(users, messages, settings)
        undeliv_msgs = get_new_messages(sender)
        return chat_pb2.SendMessageResponse(
            status="success", undeliv_messages=undeliv_msgs
        )

    def GetUndelivered(self, request, context):
        username = request.username.strip()
        num_msgs = request.num_messages
        delivered_msgs = []
        to_remove = []
        count = num_msgs
        for idx, msg_obj in enumerate(messages["undelivered"]):
            if count == 0:
                break
            if msg_obj["receiver"] == username:
                delivered_msgs.append(
                    chat_pb2.Message(
                        id=msg_obj["id"],
                        sender=msg_obj["sender"],
                        message=msg_obj["message"],
                    )
                )
                messages["delivered"].append(msg_obj)
                to_remove.append(idx)
                count -= 1
        for idx in sorted(to_remove, reverse=True):
            del messages["undelivered"][idx]
        database_wrapper.save_database(users, messages, settings)
        if not delivered_msgs:
            return chat_pb2.GetUndeliveredResponse(
                status="error", message="No undelivered messages", messages=[]
            )
        return chat_pb2.GetUndeliveredResponse(
            status="success", message="Messages retrieved", messages=delivered_msgs
        )

    def GetDelivered(self, request, context):
        username = request.username.strip()
        num_msgs = request.num_messages
        delivered_msgs = []
        count = num_msgs
        for msg_obj in messages["delivered"]:
            if count == 0:
                break
            if msg_obj["receiver"] == username:
                delivered_msgs.append(
                    chat_pb2.Message(
                        id=msg_obj["id"],
                        sender=msg_obj["sender"],
                        message=msg_obj["message"],
                    )
                )
                count -= 1
        if not delivered_msgs:
            return chat_pb2.GetDeliveredResponse(
                status="error", message="No delivered messages", messages=[]
            )
        return chat_pb2.GetDeliveredResponse(
            status="success", message="Messages retrieved", messages=delivered_msgs
        )

    def DeleteAccount(self, request, context):
        username = request.username.strip()
        if username not in users:
            return chat_pb2.DeleteAccountResponse(
                status="error", message="Account does not exist"
            )
        del users[username]
        messages["delivered"] = [
            msg
            for msg in messages["delivered"]
            if msg["sender"] != username and msg["receiver"] != username
        ]
        messages["undelivered"] = [
            msg
            for msg in messages["undelivered"]
            if msg["sender"] != username and msg["receiver"] != username
        ]
        database_wrapper.save_database(users, messages, settings)
        return chat_pb2.DeleteAccountResponse(
            status="success", message="Account deleted."
        )

    def SearchUsers(self, request, context):
        pattern = request.pattern if request.pattern else "*"
        matched = fnmatch.filter(users.keys(), pattern)
        return chat_pb2.SearchUsersResponse(status="success", users=matched)

    def DeleteMessage(self, request, context):
        username = request.username.strip()
        msg_ids = set(request.message_ids)
        before_count = len(messages["delivered"])
        messages["delivered"] = [
            msg
            for msg in messages["delivered"]
            if not (msg["receiver"] == username and msg["id"] in msg_ids)
        ]
        after_count = len(messages["delivered"])
        database_wrapper.save_database(users, messages, settings)
        undeliv_messages = get_new_messages(username)
        return chat_pb2.DeleteMessageResponse(
            status="success",
            message=f"Deleted {before_count - after_count} messages.",
            undeliv_messages=undeliv_messages,
        )

    def RefreshHome(self, request, context):
        username = request.username.strip()
        undeliv_msgs = get_new_messages(username)
        return chat_pb2.RefreshHomeResponse(
            status="success", message="Home refreshed", undeliv_messages=undeliv_msgs
        )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_ChatServiceServicer_to_server(ChatServiceServicer(), server)
    server.add_insecure_port(f"{settings['host']}:{settings['port']}")
    server.start()
    print(f"Server started on {settings['host']}:{settings['port']}")
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    serve()
