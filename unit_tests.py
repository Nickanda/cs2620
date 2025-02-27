import os
import json
import shutil
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import grpc
import tkinter as tk

# Import modules from your project.
import database_wrapper
import server
import chat_pb2
import chat_pb2_grpc


# -------------------------------
# Unit Tests for database_wrapper.py
# -------------------------------
class TestDatabaseWrapper(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for our test database.
        self.test_dir = tempfile.TemporaryDirectory()
        # Save the original file paths.
        self.orig_users_path = database_wrapper.users_database_path
        self.orig_messages_path = database_wrapper.messages_database_path
        self.orig_settings_path = database_wrapper.settings_database_path
        # Override file paths to use our temporary directory.
        database_wrapper.users_database_path = os.path.join(
            self.test_dir.name, "users.json"
        )
        database_wrapper.messages_database_path = os.path.join(
            self.test_dir.name, "messages.json"
        )
        database_wrapper.settings_database_path = os.path.join(
            self.test_dir.name, "settings.json"
        )

    def tearDown(self):
        # Restore original file paths.
        database_wrapper.users_database_path = self.orig_users_path
        database_wrapper.messages_database_path = self.orig_messages_path
        database_wrapper.settings_database_path = self.orig_settings_path
        self.test_dir.cleanup()

    def test_safe_load_missing_file(self):
        default_value = {}
        # File does not exist so safe_load should return default_value and create the file.
        result = database_wrapper.safe_load(
            database_wrapper.users_database_path, default_value
        )
        self.assertEqual(result, default_value)
        self.assertTrue(os.path.exists(database_wrapper.users_database_path))

    def test_save_and_load_database(self):
        users = {"test": {"password": "pass", "logged_in": False, "addr": 0}}
        messages = {"undelivered": [], "delivered": []}
        settings = {"counter": 10, "host": "127.0.0.1", "port": 54400}
        database_wrapper.save_database(users, messages, settings)
        # Now load the database and verify.
        loaded_users, loaded_messages, loaded_settings = (
            database_wrapper.load_database()
        )
        self.assertEqual(loaded_users, users)
        self.assertEqual(loaded_messages, messages)
        self.assertEqual(loaded_settings.get("counter"), 10)

    def test_load_client_database(self):
        settings = {
            "counter": 0,
            "host": "127.0.0.1",
            "port": 54400,
            "host_json": "127.0.0.1",
            "port_json": 54444,
        }
        with open(database_wrapper.settings_database_path, "w") as f:
            json.dump(settings, f)
        client_settings = database_wrapper.load_client_database()
        self.assertEqual(client_settings, settings)


# -------------------------------
# Unit Tests for server.py functions (RPC methods)
# -------------------------------
# Create a dummy context for testing.
class DummyContext:
    def set_details(self, details):
        self.details = details


class TestServerFunctions(unittest.TestCase):
    def setUp(self):
        # Reset global state in server module.
        users = {}
        messages = {"undelivered": [], "delivered": []}
        settings = {"counter": 0, "host": "127.0.0.1", "port": 54400}
        self.servicer = server.ChatServiceServicer(users, messages, settings)
        self.context = DummyContext()

    def test_create_account_success(self):
        req = chat_pb2.CreateAccountRequest(username="TestUser", password="pass")
        res = self.servicer.CreateAccount(req, self.context)
        self.assertEqual(res.status, "success")
        self.assertIn("TestUser", self.servicer.users)

    def test_create_account_invalid_username(self):
        req = chat_pb2.CreateAccountRequest(username="Invalid@", password="pass")
        res = self.servicer.CreateAccount(req, self.context)
        self.assertEqual(res.status, "error")

    def test_create_account_empty_password(self):
        req = chat_pb2.CreateAccountRequest(username="User2", password="")
        res = self.servicer.CreateAccount(req, self.context)
        self.assertEqual(res.status, "error")

    def test_login_nonexistent(self):
        req = chat_pb2.LoginRequest(username="NonExistent", password="pass")
        res = self.servicer.Login(req, self.context)
        self.assertEqual(res.status, "error")

    def test_login_already_logged_in(self):
        create_req = chat_pb2.CreateAccountRequest(username="User3", password="pass")
        self.servicer.CreateAccount(create_req, self.context)
        # Account is created and marked as logged in.
        login_req = chat_pb2.LoginRequest(username="User3", password="pass")
        res = self.servicer.Login(login_req, self.context)
        self.assertEqual(res.status, "error")

    def test_logout(self):
        create_req = chat_pb2.CreateAccountRequest(username="User4", password="pass")
        self.servicer.CreateAccount(create_req, self.context)
        logout_req = chat_pb2.LogoutRequest(username="User4")
        res = self.servicer.Logout(logout_req, self.context)
        self.assertEqual(res.status, "success")
        self.assertFalse(self.servicer.users["User4"]["logged_in"])

    def test_send_message_receiver_nonexistent(self):
        self.servicer.CreateAccount(
            chat_pb2.CreateAccountRequest(username="Sender", password="pass"),
            self.context,
        )
        req = chat_pb2.SendMessageRequest(
            sender="Sender", receiver="NoUser", message="Hello"
        )
        res = self.servicer.SendMessage(req, self.context)
        self.assertEqual(res.status, "error")

    def test_send_message_delivered_vs_undelivered(self):
        self.servicer.CreateAccount(
            chat_pb2.CreateAccountRequest(username="Sender2", password="pass"),
            self.context,
        )
        self.servicer.CreateAccount(
            chat_pb2.CreateAccountRequest(username="Receiver2", password="pass"),
            self.context,
        )
        # Simulate offline: set logged_in False.
        self.servicer.users["Receiver2"]["logged_in"] = False
        req_offline = chat_pb2.SendMessageRequest(
            sender="Sender2", receiver="Receiver2", message="Offline Message"
        )
        res_offline = self.servicer.SendMessage(req_offline, self.context)
        self.assertEqual(res_offline.status, "success")
        self.assertEqual(len(self.servicer.messages["undelivered"]), 1)
        # Now simulate online.
        self.servicer.users["Receiver2"]["logged_in"] = True
        req_online = chat_pb2.SendMessageRequest(
            sender="Sender2", receiver="Receiver2", message="Online Message"
        )
        res_online = self.servicer.SendMessage(req_online, self.context)
        self.assertEqual(res_online.status, "success")
        self.assertEqual(len(self.servicer.messages["delivered"]), 1)

    def test_get_undelivered(self):
        self.servicer.CreateAccount(
            chat_pb2.CreateAccountRequest(username="User5", password="pass"),
            self.context,
        )
        msg = {"id": 1, "sender": "Sender", "receiver": "User5", "message": "Test"}
        self.servicer.messages["undelivered"].append(msg)
        req = chat_pb2.GetUndeliveredRequest(username="User5", num_messages=1)
        res = self.servicer.GetUndelivered(req, self.context)
        self.assertEqual(res.status, "success")
        self.assertEqual(len(res.messages), 1)
        # The message should now be moved to delivered.
        self.assertEqual(len(self.servicer.messages["undelivered"]), 0)
        self.assertEqual(len(self.servicer.messages["delivered"]), 1)

    def test_get_delivered(self):
        self.servicer.CreateAccount(
            chat_pb2.CreateAccountRequest(username="User6", password="pass"),
            self.context,
        )
        msg = {
            "id": 2,
            "sender": "Sender",
            "receiver": "User6",
            "message": "Delivered Test",
        }
        self.servicer.messages["delivered"].append(msg)
        req = chat_pb2.GetDeliveredRequest(username="User6", num_messages=1)
        res = self.servicer.GetDelivered(req, self.context)
        self.assertEqual(res.status, "success")
        self.assertEqual(len(res.messages), 1)

    def test_delete_account(self):
        self.servicer.CreateAccount(
            chat_pb2.CreateAccountRequest(username="User7", password="pass"),
            self.context,
        )
        msg1 = {"id": 3, "sender": "User7", "receiver": "Other", "message": "Msg1"}
        msg2 = {"id": 4, "sender": "Other", "receiver": "User7", "message": "Msg2"}
        self.servicer.messages["delivered"].extend([msg1, msg2])
        req = chat_pb2.DeleteAccountRequest(username="User7")
        res = self.servicer.DeleteAccount(req, self.context)
        self.assertEqual(res.status, "success")
        self.assertNotIn("User7", self.servicer.users)
        for msg in self.servicer.messages["delivered"]:
            self.assertNotIn("User7", [msg["sender"], msg["receiver"]])

    def test_search_users(self):
        self.servicer.CreateAccount(
            chat_pb2.CreateAccountRequest(username="Alpha", password="pass"),
            self.context,
        )
        self.servicer.CreateAccount(
            chat_pb2.CreateAccountRequest(username="Beta", password="pass"),
            self.context,
        )
        self.servicer.CreateAccount(
            chat_pb2.CreateAccountRequest(username="Alfred", password="pass"),
            self.context,
        )
        req = chat_pb2.SearchUsersRequest(pattern="Al*")
        res = self.servicer.SearchUsers(req, self.context)
        self.assertEqual(res.status, "success")
        self.assertIn("Alpha", res.users)
        self.assertIn("Alfred", res.users)
        self.assertNotIn("Beta", res.users)

    def test_delete_messages(self):
        self.servicer.CreateAccount(
            chat_pb2.CreateAccountRequest(username="User8", password="pass"),
            self.context,
        )
        msg = {
            "id": 5,
            "sender": "Other",
            "receiver": "User8",
            "message": "To be deleted",
        }
        self.servicer.messages["delivered"].append(msg)
        req = chat_pb2.DeleteMessageRequest(username="User8", message_ids=[5])
        res = self.servicer.DeleteMessage(req, self.context)
        self.assertEqual(res.status, "success")
        for m in self.servicer.messages["delivered"]:
            self.assertNotEqual(m["id"], 5)

    def test_refresh_home(self):
        self.servicer.CreateAccount(
            chat_pb2.CreateAccountRequest(username="User9", password="pass"),
            self.context,
        )
        msg = {
            "id": 6,
            "sender": "Sender",
            "receiver": "User9",
            "message": "Refresh home",
        }
        self.servicer.messages["undelivered"].append(msg)
        req = chat_pb2.RefreshHomeRequest(username="User9")
        res = self.servicer.RefreshHome(req, self.context)
        self.assertEqual(res.status, "success")
        self.assertEqual(res.undeliv_messages, 1)


# -------------------------------
# Unit Tests for GUI/Screen Functions (screens_rpc modules)
# We simulate stub responses and use dummy root objects.
# -------------------------------
# For these tests we import the screen modules.
import screens_rpc.delete_messages
import screens_rpc.login
import screens_rpc.messages
import screens_rpc.send_message
import screens_rpc.signup
import screens_rpc.user_list


# Create dummy stub and root objects.
class DummyStub:
    def DeleteMessage(self, request):
        class Response:
            status = "success"
            message = "Deleted successfully"
            undeliv_messages = 0

        return Response()

    def Logout(self, request):
        class Response:
            status = "success"
            message = "Logged out"

        return Response()

    def Login(self, request):
        class Response:
            status = "success"
            message = "Logged in"
            undelivered_count = 0

        return Response()

    def RefreshHome(self, request):
        class Response:
            status = "success"
            message = "Home refreshed"
            undeliv_messages = 0

        return Response()

    def SendMessage(self, request):
        class Response:
            status = "success"
            message = "Message sent"
            undeliv_messages = 0

        return Response()

    def SearchUsers(self, request):
        class Response:
            status = "success"
            users = ["Alice", "Bob"]

        return Response()

    def CreateAccount(self, request):
        class Response:
            status = "success"
            message = "Account created"

        return Response()


class DummyRoot:
    def __init__(self):
        self.destroy_called = False

    def destroy(self):
        self.destroy_called = True

    def mainloop(self):
        pass


# --- Delete Message Screen ---
class TestScreensDeleteMessage(unittest.TestCase):
    def setUp(self):
        self.stub = DummyStub()
        self.root = DummyRoot()
        self.tk_root = tk.Tk()
        self.current_user = "TestUser"

    def tearDown(self):
        self.tk_root.destroy()

    @patch("screens_rpc.delete_messages.messagebox.showerror")
    def test_delete_message_empty_input(self, mock_showerror):
        var = tk.StringVar(self.tk_root, value="")
        result = screens_rpc.delete_messages.delete_message(
            self.stub, self.root, var, self.current_user
        )
        mock_showerror.assert_called_once()
        self.assertIsNone(result)

    @patch("screens_rpc.delete_messages.messagebox.showerror")
    def test_delete_message_valid_input(self, mock_showerror):
        var = tk.StringVar(self.tk_root, value="1,2,3")
        result = screens_rpc.delete_messages.delete_message(
            self.stub, self.root, var, self.current_user
        )
        mock_showerror.assert_not_called()
        self.assertIsNotNone(result)
        self.assertEqual(result["command"], "refresh_home")


# --- Login Screen ---
class TestScreensLogin(unittest.TestCase):
    def setUp(self):
        self.stub = DummyStub()
        self.root = DummyRoot()
        self.tk_root = tk.Tk()
        self.username_var = tk.StringVar(self.tk_root, value="ValidUser")
        self.password_var = tk.StringVar(self.tk_root, value="ValidPass")

    def tearDown(self):
        self.tk_root.destroy()

    @patch("screens_rpc.login.messagebox.showerror")
    def test_login_empty_fields(self, mock_showerror):
        self.username_var.set("")
        result = screens_rpc.login.login(
            self.stub, self.root, self.username_var, self.password_var
        )
        mock_showerror.assert_called_once()
        self.assertIsNone(result)

    @patch("screens_rpc.login.messagebox.showerror")
    def test_login_invalid_username(self, mock_showerror):
        self.username_var.set("Invalid@User")
        result = screens_rpc.login.login(
            self.stub, self.root, self.username_var, self.password_var
        )
        mock_showerror.assert_called_once()
        self.assertIsNone(result)

    @patch("screens_rpc.login.messagebox.showerror")
    def test_login_success(self, mock_showerror):
        result = screens_rpc.login.login(
            self.stub, self.root, self.username_var, self.password_var
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["command"], "login")


# --- Send Message Screen ---
class TestScreensSendMessage(unittest.TestCase):
    def setUp(self):
        self.stub = DummyStub()
        self.root = DummyRoot()
        self.tk_root = tk.Tk()
        self.current_user = "UserSender"
        self.recipient_var = tk.StringVar(self.tk_root, value="ValidRecipient")
        self.message_widget = tk.Text(self.tk_root)
        self.message_widget.insert("1.0", "Hello there!")

    def tearDown(self):
        self.tk_root.destroy()

    @patch("screens_rpc.send_message.messagebox.showerror")
    def test_send_message_empty_recipient(self, mock_showerror):
        self.recipient_var.set("")
        result = screens_rpc.send_message.send_message(
            self.stub,
            self.root,
            self.recipient_var,
            self.message_widget,
            self.current_user,
        )
        mock_showerror.assert_called_once()
        self.assertIsNone(result)

    @patch("screens_rpc.send_message.messagebox.showerror")
    def test_send_message_invalid_recipient(self, mock_showerror):
        self.recipient_var.set("Invalid@Recipient")
        result = screens_rpc.send_message.send_message(
            self.stub,
            self.root,
            self.recipient_var,
            self.message_widget,
            self.current_user,
        )
        mock_showerror.assert_called_once()
        self.assertIsNone(result)

    @patch("screens_rpc.send_message.messagebox.showerror")
    def test_send_message_success(self, mock_showerror):
        result = screens_rpc.send_message.send_message(
            self.stub,
            self.root,
            self.recipient_var,
            self.message_widget,
            self.current_user,
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["command"], "refresh_home")


# --- Signup Screen ---
class TestScreensSignup(unittest.TestCase):
    def setUp(self):
        self.stub = DummyStub()
        self.root = DummyRoot()
        self.tk_root = tk.Tk()
        self.tk_root.withdraw()
        self.username_var = tk.StringVar(self.tk_root, value="NewUser")
        self.password_var = tk.StringVar(self.tk_root, value="NewPass")

    def tearDown(self):
        self.tk_root.destroy()

    @patch("screens_rpc.signup.messagebox.showerror")
    def test_create_user_empty_fields(self, mock_showerror):
        self.username_var.set("")
        result = screens_rpc.signup.create_user(
            self.stub, self.root, self.username_var, self.password_var
        )
        mock_showerror.assert_called_once()
        self.assertIsNone(result)

    @patch("screens_rpc.signup.messagebox.showerror")
    def test_create_user_invalid_username(self, mock_showerror):
        self.username_var.set("Invalid@User")
        result = screens_rpc.signup.create_user(
            self.stub, self.root, self.username_var, self.password_var
        )
        mock_showerror.assert_called_once()
        self.assertIsNone(result)

    @patch("screens_rpc.signup.messagebox.showerror")
    def test_create_user_success(self, mock_showerror):
        result = screens_rpc.signup.create_user(
            self.stub, self.root, self.username_var, self.password_var
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["command"], "login")


# --- User List Screen ---
class TestScreensUserList(unittest.TestCase):
    def setUp(self):
        self.stub = DummyStub()
        self.root = DummyRoot()
        self.tk_root = tk.Tk()
        self.username = "UserListTest"
        self.search_var = tk.StringVar(self.tk_root, value="Ali*")

    def tearDown(self):
        self.tk_root.destroy()

    @patch("screens_rpc.user_list.messagebox.showerror")
    def test_search_invalid_characters(self, mock_showerror):
        self.search_var.set("Invalid#")
        result = screens_rpc.user_list.search(self.stub, self.root, self.search_var)
        mock_showerror.assert_called_once()
        self.assertIsNone(result)

    @patch("screens_rpc.user_list.messagebox.showerror")
    def test_search_success(self, mock_showerror):
        self.search_var.set("Ali*")
        result = screens_rpc.user_list.search(self.stub, self.root, self.search_var)
        self.assertIsNotNone(result)
        self.assertEqual(result["command"], "user_list")


if __name__ == "__main__":
    unittest.main()
