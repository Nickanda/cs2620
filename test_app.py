import os
import selectors
import types
import tempfile
import unittest
import tkinter as tk
from tkinter import messagebox
from unittest.mock import patch, MagicMock
from argon2 import PasswordHasher

# Import the modules to test.
import main
import database_wrapper
import screens.delete_messages as delete_messages
import screens.home as home
import screens.login as login_screen
import screens.messages as messages_screen
import screens.send_message as send_message_screen
import screens.signup as signup_screen
import screens.user_list as user_list_screen

###############################################################################
# Dummy classes to simulate sockets and Tk windows without real network/UI
###############################################################################

class DummySocket:
    """A dummy socket to record sent data (for main.py tests)."""
    def __init__(self):
        self.sent = []
    def send(self, message):
        self.sent.append(message)
        return len(message)
    def sendall(self, message):
        self.sent.append(message)
    def recv(self, bufsize):
        # For testing, we return an empty byte string.
        return b""
    def close(self):
        pass

class DummySocketForScreens:
    """A dummy socket to record calls to sendall (for screens tests)."""
    def __init__(self):
        self.sent = []
    def sendall(self, message):
        self.sent.append(message)

class DummyTk:
    """A dummy replacement for a Tk window."""
    def __init__(self):
        self.destroy_called = False
    def destroy(self):
        self.destroy_called = True
    def mainloop(self):
        pass

###############################################################################
# Tests for main.py (the server command processing)
###############################################################################

class TestMainServiceConnection(unittest.TestCase):
    def setUp(self):
        # Reset globals used by main.py
        main.users = {}
        main.messages = {"undelivered": [], "delivered": []}
        main.settings = {"counter": 0}
        # Patch database_wrapper.save_database to avoid file I/O during tests.
        self.save_patch = patch('database_wrapper.save_database', lambda users, messages, settings: None)
        self.save_patch.start()
        self.hasher = PasswordHasher()

    def tearDown(self):
        self.save_patch.stop()

    def run_service(self, command_str, mask=selectors.EVENT_WRITE):
        """Helper: pre-populate outb with a command and call service_connection."""
        dummy_sock = DummySocket()
        data = types.SimpleNamespace(addr=("127.0.0.1", 12345), inb=b"", outb=command_str.encode("utf-8"))
        key = types.SimpleNamespace(fileobj=dummy_sock, data=data)
        main.service_connection(key, mask)
        return dummy_sock, data

    def test_create_invalid_username(self):
        # Non-alphanumeric username should return an error.
        sock, _ = self.run_service("create inv@lid somehash")
        self.assertTrue(any(b"error Username must be alphanumeric" in sent for sent in sock.sent))
    
    def test_create_existing_username(self):
        # Create a user beforehand.
        main.users["testuser"] = {"password": self.hasher.hash("password"), "logged_in": True, "addr": 1111}
        sock, _ = self.run_service("create testuser somehash")
        self.assertTrue(any(b"error Username already exists" in sent for sent in sock.sent))

    def test_create_empty_username(self):
        sock, _ = self.run_service("create  somehash")
        self.assertTrue(any(b"error Username must be alphanumeric" in sent for sent in sock.sent))

    def test_create_empty_password(self):
        sock, _ = self.run_service("create validuser ")
        self.assertTrue(any(b"error Username must be alphanumeric" in sent for sent in sock.sent))

    def test_login_empty_username(self):
        sock, _ = self.run_service("login  password")
        self.assertTrue(any(b"error Username does not exist" in sent for sent in sock.sent))

    def test_login_empty_password(self):
        main.users["validuser"] = {"password": self.hasher.hash("secret"), "logged_in": False, "addr": 0}
        sock, _ = self.run_service("login validuser ")
        self.assertTrue(any(b"error Incorrect password" in sent for sent in sock.sent))

    def test_create_success(self):
        # Creating a new account should succeed.
        sock, _ = self.run_service("create newuser somehash")
        self.assertTrue(any(b"login newuser 0" in sent for sent in sock.sent))
        self.assertIn("newuser", main.users)
        self.assertTrue(main.users["newuser"]["logged_in"])

    def test_login_nonexistent(self):
        sock, _ = self.run_service("login unknown password")
        self.assertTrue(any(b"error Username does not exist" in sent for sent in sock.sent))

    def test_login_incorrect_password(self):
        hashed = self.hasher.hash("correct")
        main.users["testuser"] = {"password": hashed, "logged_in": False, "addr": 0}
        sock, _ = self.run_service("login testuser wrong")
        self.assertTrue(any(b"error Incorrect password" in sent for sent in sock.sent))

    def test_login_already_logged_in(self):
        hashed = self.hasher.hash("secret")
        main.users["testuser"] = {"password": hashed, "logged_in": True, "addr": 2222}
        sock, _ = self.run_service("login testuser secret")
        self.assertTrue(any(b"error User already logged in" in sent for sent in sock.sent))

    def test_login_success(self):
        hashed = self.hasher.hash("secret")
        main.users["testuser"] = {"password": hashed, "logged_in": False, "addr": 0}
        # Add an undelivered message for testuser.
        main.messages["undelivered"].append({"id": 1, "sender": "other", "receiver": "testuser", "message": "Hello"})
        sock, _ = self.run_service("login testuser secret")
        self.assertTrue(any(b"login testuser 1" in sent for sent in sock.sent))
        self.assertTrue(main.users["testuser"]["logged_in"])

    def test_logout_nonexistent(self):
        sock, _ = self.run_service("logout unknown")
        self.assertTrue(any(b"error Username does not exist" in sent for sent in sock.sent))

    def test_logout_success(self):
        main.users["testuser"] = {"password": self.hasher.hash("secret"), "logged_in": True, "addr": 3333}
        sock, _ = self.run_service("logout testuser")
        self.assertTrue(any(b"logout" in sent for sent in sock.sent))
        self.assertFalse(main.users["testuser"]["logged_in"])

    def test_search(self):
        # Setup a few users.
        main.users = {
            "alice": {"password": "x", "logged_in": False, "addr": 0},
            "bob": {"password": "x", "logged_in": False, "addr": 0},
            "charlie": {"password": "x", "logged_in": False, "addr": 0}
        }
        sock, _ = self.run_service("search a*")
        # Expected to match "alice"
        self.assertTrue(any(b"user_list alice" in sent for sent in sock.sent))

    def test_delete_acct(self):
        main.users = {
            "testuser": {"password": self.hasher.hash("secret"), "logged_in": True, "addr": 4444},
            "other": {"password": "x", "logged_in": False, "addr": 0}
        }
        # Add some messages that involve testuser.
        main.messages["delivered"] = [
            {"id": 1, "sender": "testuser", "receiver": "other", "message": "Hi"},
            {"id": 2, "sender": "other", "receiver": "testuser", "message": "Hello"}
        ]
        main.messages["undelivered"] = [
            {"id": 3, "sender": "testuser", "receiver": "other", "message": "Test"}
        ]
        sock, _ = self.run_service("delete_acct testuser")
        self.assertNotIn("testuser", main.users)
        for msg in main.messages["delivered"]:
            self.assertNotEqual(msg["sender"], "testuser")
            self.assertNotEqual(msg["receiver"], "testuser")
        for msg in main.messages["undelivered"]:
            self.assertNotEqual(msg["sender"], "testuser")
            self.assertNotEqual(msg["receiver"], "testuser")

    def test_send_msg_invalid_receiver(self):
        main.users = {"sender": {"password": self.hasher.hash("secret"), "logged_in": True, "addr": 5555}}
        sock, _ = self.run_service("send_msg sender unknown Hello")
        self.assertTrue(any(b"error Receiver does not exist" in sent for sent in sock.sent))

    def test_send_msg_delivered(self):
        main.users = {
            "sender": {"password": self.hasher.hash("secret"), "logged_in": True, "addr": 6666},
            "receiver": {"password": "x", "logged_in": True, "addr": 7777}
        }
        initial_delivered = len(main.messages["delivered"])
        sock, _ = self.run_service("send_msg sender receiver Hi there")
        self.assertEqual(len(main.messages["delivered"]), initial_delivered + 1)
        self.assertTrue(any(b"refresh_home" in sent for sent in sock.sent))

    def test_send_msg_undelivered(self):
        main.users = {
            "sender": {"password": self.hasher.hash("secret"), "logged_in": True, "addr": 8888},
            "receiver": {"password": "x", "logged_in": False, "addr": 0}
        }
        initial_undelivered = len(main.messages["undelivered"])
        sock, _ = self.run_service("send_msg sender receiver Hello")
        self.assertEqual(len(main.messages["undelivered"]), initial_undelivered + 1)
        self.assertTrue(any(b"refresh_home" in sent for sent in sock.sent))

    def test_get_undelivered(self):
        # Setup some undelivered messages.
        main.messages["undelivered"] = [
            {"id": 1, "sender": "alice", "receiver": "testuser", "message": "Msg1"},
            {"id": 2, "sender": "bob", "receiver": "testuser", "message": "Msg2"},
            {"id": 3, "sender": "charlie", "receiver": "other", "message": "Msg3"}
        ]
        sock, _ = self.run_service("get_undelivered testuser 2")
        delivered_ids = [msg["id"] for msg in main.messages["delivered"]]
        self.assertIn(1, delivered_ids)
        self.assertIn(2, delivered_ids)
        self.assertEqual(len(main.messages["undelivered"]), 1)
        self.assertTrue(any(b"messages" in sent for sent in sock.sent))

    def test_get_delivered(self):
        main.messages["delivered"] = [
            {"id": 10, "sender": "alice", "receiver": "testuser", "message": "Msg10"},
            {"id": 11, "sender": "bob", "receiver": "testuser", "message": "Msg11"},
            {"id": 12, "sender": "charlie", "receiver": "other", "message": "Msg12"}
        ]
        sock, _ = self.run_service("get_delivered testuser 1")
        self.assertTrue(any(b"messages" in sent for sent in sock.sent))

    def test_refresh_home(self):
        main.messages["undelivered"] = [
            {"id": 5, "sender": "x", "receiver": "testuser", "message": "Msg5"},
            {"id": 6, "sender": "y", "receiver": "testuser", "message": "Msg6"}
        ]
        sock, _ = self.run_service("refresh_home testuser")
        self.assertTrue(any(b"refresh_home 2" in sent for sent in sock.sent))

    def test_delete_msg(self):
        main.messages["delivered"] = [
            {"id": 20, "sender": "alice", "receiver": "testuser", "message": "Msg20"},
            {"id": 21, "sender": "bob", "receiver": "testuser", "message": "Msg21"},
            {"id": 22, "sender": "charlie", "receiver": "other", "message": "Msg22"}
        ]
        sock, _ = self.run_service("delete_msg testuser 20,21")
        for msg in main.messages["delivered"]:
            self.assertNotIn(msg["id"], [20, 21])
        self.assertTrue(any(b"refresh_home" in sent for sent in sock.sent))

    def test_delete_nonexistent_account(self):
        sock, _ = self.run_service("delete_acct nonexistent")
        self.assertTrue(any(b"error Username does not exist" in sent for sent in sock.sent))

    def test_delete_account_with_messages(self):
        main.users["victim"] = {"password": self.hasher.hash("pass123"), "logged_in": False, "addr": 0}
        main.messages["undelivered"].append({"id": 1, "sender": "other", "receiver": "victim", "message": "Message1"})
        main.messages["delivered"].append({"id": 2, "sender": "victim", "receiver": "other", "message": "Message2"})
        sock, _ = self.run_service("delete_acct victim")
        self.assertNotIn("victim", main.users)
        self.assertFalse(any(msg["receiver"] == "victim" for msg in main.messages["undelivered"]))
        self.assertFalse(any(msg["sender"] == "victim" for msg in main.messages["delivered"]))
        self.assertTrue(any(b"logout" in sent for sent in sock.sent))

    def test_send_message_empty_content(self):
        main.users["sender"] = {"password": self.hasher.hash("secret"), "logged_in": True, "addr": 0}
        main.users["receiver"] = {"password": self.hasher.hash("secret"), "logged_in": True, "addr": 0}
        sock, _ = self.run_service("send_msg sender receiver ")
        self.assertTrue(any(b"error Message cannot be empty" in sent for sent in sock.sent))

    def test_send_message_to_self(self):
        main.users["sender"] = {"password": self.hasher.hash("secret"), "logged_in": True, "addr": 0}
        sock, _ = self.run_service("send_msg sender sender Hi")
        self.assertTrue(any(b"error Cannot send message to yourself" in sent for sent in sock.sent))

    def test_get_undelivered_zero_messages(self):
        sock, _ = self.run_service("get_undelivered user 0")
        self.assertTrue(any(b"error Number of messages must be greater than 0" in sent for sent in sock.sent))

    def test_get_delivered_zero_messages(self):
        sock, _ = self.run_service("get_delivered user 0")
        self.assertTrue(any(b"error Number of messages must be greater than 0" in sent for sent in sock.sent))

    def test_delete_message_not_owned(self):
        main.messages["delivered"].append({"id": 99, "sender": "someone", "receiver": "victim", "message": "Hidden"})
        sock, _ = self.run_service("delete_msg victim 99")
        self.assertTrue(any(b"error Cannot delete messages you do not own" in sent for sent in sock.sent))

###############################################################################
# Tests for database_wrapper.py
###############################################################################

class TestDatabaseWrapper(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for the JSON files.
        self.test_dir = tempfile.TemporaryDirectory()
        self.orig_users_path = database_wrapper.users_database_path
        self.orig_messages_path = database_wrapper.messages_database_path
        self.orig_settings_path = database_wrapper.settings_database_path
        database_wrapper.users_database_path = os.path.join(self.test_dir.name, "users.json")
        database_wrapper.messages_database_path = os.path.join(self.test_dir.name, "messages.json")
        database_wrapper.settings_database_path = os.path.join(self.test_dir.name, "settings.json")

    def tearDown(self):
        self.test_dir.cleanup()
        database_wrapper.users_database_path = self.orig_users_path
        database_wrapper.messages_database_path = self.orig_messages_path
        database_wrapper.settings_database_path = self.orig_settings_path

    def test_load_database_creates_files(self):
        # Remove files if they exist.
        for path in [database_wrapper.users_database_path,
                     database_wrapper.messages_database_path,
                     database_wrapper.settings_database_path]:
            if os.path.exists(path):
                os.remove(path)
        users, messages, settings = database_wrapper.load_database()
        self.assertEqual(users, {})
        self.assertEqual(messages, {"undelivered": [], "delivered": []})
        self.assertEqual(settings, {"counter": 0})

    def test_save_and_load_database(self):
        users = {"user1": {"password": "hash", "logged_in": False, "addr": 0}}
        messages = {"undelivered": [{"id": 1, "sender": "user2", "receiver": "user1", "message": "Hi"}],
                    "delivered": []}
        settings = {"counter": 1}
        database_wrapper.save_database(users, messages, settings)
        loaded_users, loaded_messages, loaded_settings = database_wrapper.load_database()
        self.assertEqual(users, loaded_users)
        self.assertEqual(messages, loaded_messages)
        self.assertEqual(settings, loaded_settings)

    def test_load_corrupted_users_file(self):
        with open(database_wrapper.users_database_path, "w") as f:
            f.write("{invalid_json}")  # Corrupted file
        users, messages, settings = database_wrapper.load_database()
        self.assertEqual(users, {})  # Should recover with an empty dictionary

    def test_load_corrupted_messages_file(self):
        with open(database_wrapper.messages_database_path, "w") as f:
            f.write("{invalid_json}")  # Corrupted file
        users, messages, settings = database_wrapper.load_database()
        self.assertEqual(messages, {"undelivered": [], "delivered": []})

    def test_load_corrupted_settings_file(self):
        with open(database_wrapper.settings_database_path, "w") as f:
            f.write("{invalid_json}")  # Corrupted file
        users, messages, settings = database_wrapper.load_database()
        self.assertEqual(settings, {"counter": 0})

###############################################################################
# Tests for the screens (UI modules)
###############################################################################

# For screens tests we create dummy sockets and a dummy root.

class TestScreensSignup(unittest.TestCase):
    def setUp(self):
        self.dummy_socket = DummySocketForScreens()
        self.root = DummyTk()
        # Create a hidden Tk instance for StringVars.
        self.tk_root = tk.Tk()
        self.tk_root.withdraw()
    def tearDown(self):
        self.tk_root.destroy()
    def test_create_user_valid(self):
        username_var = tk.StringVar(self.tk_root, value="testuser")
        password_var = tk.StringVar(self.tk_root, value="secret")
        with patch('screens.signup.messagebox.showerror') as mock_showerror:
            signup_screen.create_user(self.dummy_socket, self.root, username_var, password_var)
            # Expect a message starting with "create testuser "
            self.assertTrue(any(msg.startswith(b"create testuser ") for msg in self.dummy_socket.sent))
            self.assertTrue(self.root.destroy_called)
            mock_showerror.assert_not_called()
    def test_create_user_invalid_username(self):
        username_var = tk.StringVar(self.tk_root, value="test*user")
        password_var = tk.StringVar(self.tk_root, value="secret")
        with patch('screens.signup.messagebox.showerror') as mock_showerror:
            signup_screen.create_user(self.dummy_socket, self.root, username_var, password_var)
            mock_showerror.assert_called_once_with("Error", "Username must be alphanumeric")

class TestScreensLogin(unittest.TestCase):
    def setUp(self):
        self.dummy_socket = DummySocketForScreens()
        self.root = DummyTk()
        self.tk_root = tk.Tk()
        self.tk_root.withdraw()
    def tearDown(self):
        self.tk_root.destroy()
    def test_login_valid(self):
        username_var = tk.StringVar(self.tk_root, value="testuser")
        password_var = tk.StringVar(self.tk_root, value="secret")
        with patch('screens.login.messagebox.showerror') as mock_showerror:
            login_screen.login(self.dummy_socket, self.root, username_var, password_var)
            self.assertTrue(any(msg.startswith(b"login testuser secret") for msg in self.dummy_socket.sent))
            self.assertTrue(self.root.destroy_called)
            mock_showerror.assert_not_called()
    def test_login_invalid_username(self):
        username_var = tk.StringVar(self.tk_root, value="test*user")
        password_var = tk.StringVar(self.tk_root, value="secret")
        with patch('screens.login.messagebox.showerror') as mock_showerror:
            login_screen.login(self.dummy_socket, self.root, username_var, password_var)
            mock_showerror.assert_called_once_with("Error", "Username must be alphanumeric")
    def test_login_blank_username(self):
        username_var = tk.StringVar(self.tk_root, value="")
        password_var = tk.StringVar(self.tk_root, value="password")
        with patch('screens.login.messagebox.showerror') as mock_showerror:
            login_screen.login(self.dummy_socket, self.root, username_var, password_var)
            mock_showerror.assert_called_once_with("Error", "All fields are required")

class TestScreensSendMessage(unittest.TestCase):
    def setUp(self):
        self.dummy_socket = DummySocketForScreens()
        self.root = DummyTk()
        self.tk_root = tk.Tk()
        self.tk_root.withdraw()
    def tearDown(self):
        self.tk_root.destroy()
    def test_send_message_valid(self):
        recipient_var = tk.StringVar(self.tk_root, value="receiver")
        text_widget = tk.Text(self.tk_root)
        text_widget.insert("1.0", "Hello there")
        with patch('screens.send_message.messagebox.showerror') as mock_showerror:
            send_message_screen.send_message(self.dummy_socket, self.root, recipient_var, text_widget, "sender")
            self.assertTrue(any(msg.startswith(b"send_msg sender receiver Hello there") for msg in self.dummy_socket.sent))
            self.assertTrue(self.root.destroy_called)
            mock_showerror.assert_not_called()
    def test_send_message_invalid_recipient(self):
        recipient_var = tk.StringVar(self.tk_root, value="receiver!")
        text_widget = tk.Text(self.tk_root)
        text_widget.insert("1.0", "Hello there")
        with patch('screens.send_message.messagebox.showerror') as mock_showerror:
            send_message_screen.send_message(self.dummy_socket, self.root, recipient_var, text_widget, "sender")
            mock_showerror.assert_called_once_with("Error", "Username must be alphanumeric")
    def test_send_message_blank_recipient(self):
        recipient_var = tk.StringVar(self.tk_root, value="")
        text_widget = tk.Text(self.tk_root)
        text_widget.insert("1.0", "Hello")
        with patch('screens.send_message.messagebox.showerror') as mock_showerror:
            send_message_screen.send_message(self.dummy_socket, self.root, recipient_var, text_widget, "sender")
            mock_showerror.assert_called_once_with("Error", "All fields are required")

class TestScreensDeleteMessage(unittest.TestCase):
    def setUp(self):
        self.dummy_socket = DummySocketForScreens()
        self.root = DummyTk()
        self.tk_root = tk.Tk()
        self.tk_root.withdraw()
    def tearDown(self):
        self.tk_root.destroy()
    def test_delete_message_valid(self):
        delete_ids_var = tk.StringVar(self.tk_root, value="1,2,3")
        with patch('screens.delete_message.messagebox.showerror') as mock_showerror:
            delete_messages.delete_message(self.dummy_socket, self.root, delete_ids_var, "testuser")
            self.assertTrue(any(msg.startswith(b"delete_msg testuser 1,2,3") for msg in self.dummy_socket.sent))
            self.assertTrue(self.root.destroy_called)
            mock_showerror.assert_not_called()
    def test_delete_message_invalid_ids(self):
        delete_ids_var = tk.StringVar(self.tk_root, value="1, 2,3")  # contains a space
        with patch('screens.delete_message.messagebox.showerror') as mock_showerror:
            delete_messages.delete_message(self.dummy_socket, self.root, delete_ids_var, "testuser")
            mock_showerror.assert_called_once_with("Error", "Delete IDs must be alphanumeric comma-separated list")
    def test_delete_message_invalid_input(self):
        delete_ids_var = tk.StringVar(self.tk_root, value="bad input!")
        with patch('screens.delete_message.messagebox.showerror') as mock_showerror:
            delete_message.delete_message(self.dummy_socket, self.root, delete_ids_var, "user")
            mock_showerror.assert_called_once_with("Error", "Delete IDs must be alphanumeric comma-separated list")

class TestScreensUserList(unittest.TestCase):
    def setUp(self):
        self.dummy_socket = DummySocketForScreens()
        self.root = DummyTk()
        self.tk_root = tk.Tk()
        self.tk_root.withdraw()
    def tearDown(self):
        self.tk_root.destroy()
    def test_search_valid(self):
        search_var = tk.StringVar(self.tk_root, value="alice*")
        with patch('screens.user_list.messagebox.showerror') as mock_showerror:
            user_list_screen.search(self.dummy_socket, self.root, search_var)
            self.assertTrue(any(msg.startswith(b"search alice*") for msg in self.dummy_socket.sent))
            self.assertTrue(self.root.destroy_called)
            mock_showerror.assert_not_called()
    def test_search_invalid(self):
        search_var = tk.StringVar(self.tk_root, value="alice#")
        with patch('screens.user_list.messagebox.showerror') as mock_showerror:
            user_list_screen.search(self.dummy_socket, self.root, search_var)
            mock_showerror.assert_called_once_with("Error", "Search characters must be alphanumeric or *")

class TestScreensMessages(unittest.TestCase):
    def setUp(self):
        self.dummy_socket = DummySocketForScreens()
        self.root = DummyTk()
        self.tk_root = tk.Tk()
        self.tk_root.withdraw()
    def tearDown(self):
        self.tk_root.destroy()
    def test_get_undelivered_messages_valid(self):
        num_messages_var = tk.IntVar(self.tk_root, value=2)
        with patch('screens.messages.messagebox.showerror') as mock_showerror:
            messages_screen.get_undelivered_messages(self.dummy_socket, self.root, num_messages_var, "testuser")
            self.assertTrue(any(msg.startswith(b"get_undelivered testuser 2") for msg in self.dummy_socket.sent))
            self.assertTrue(self.root.destroy_called)
            mock_showerror.assert_not_called()
    def test_get_undelivered_messages_zero(self):
        num_messages_var = tk.IntVar(self.tk_root, value=0)
        with patch('screens.messages.messagebox.showerror') as mock_showerror:
            messages_screen.get_undelivered_messages(self.dummy_socket, self.root, num_messages_var, "testuser")
            mock_showerror.assert_called_once_with("Error", "Number of messages must be greater than 0")
    def test_get_delivered_messages_valid(self):
        num_messages_var = tk.IntVar(self.tk_root, value=3)
        with patch('screens.messages.messagebox.showerror') as mock_showerror:
            messages_screen.get_delivered_messages(self.dummy_socket, self.root, num_messages_var, "testuser")
            self.assertTrue(any(msg.startswith(b"get_delivered testuser 3") for msg in self.dummy_socket.sent))
            self.assertTrue(self.root.destroy_called)
            mock_showerror.assert_not_called()

class TestScreensHome(unittest.TestCase):
    def setUp(self):
        self.dummy_socket = DummySocketForScreens()
        self.root = DummyTk()
    def test_open_read_messages(self):
        with patch('screens.home.screens.messages.launch_window') as mock_launch:
            home.open_read_messages(self.dummy_socket, self.root, "testuser")
            mock_launch.assert_called_once_with(self.dummy_socket, [], "testuser")
    def test_open_send_message(self):
        with patch('screens.home.screens.send_message.launch_window') as mock_launch:
            home.open_send_message(self.dummy_socket, self.root, "testuser")
            mock_launch.assert_called_once_with(self.dummy_socket, "testuser")
    def test_open_delete_messages(self):
        with patch('screens.home.screens.delete_messages.launch_window') as mock_launch:
            home.open_delete_messages(self.dummy_socket, self.root, "testuser")
            mock_launch.assert_called_once_with(self.dummy_socket, "testuser")
    def test_open_user_list(self):
        with patch('screens.home.screens.user_list.launch_window') as mock_launch:
            home.open_user_list(self.dummy_socket, self.root, "testuser")
            mock_launch.assert_called_once_with(self.dummy_socket, [], "testuser")
    def test_logout(self):
        home.logout(self.dummy_socket, self.root, "testuser")
        self.assertTrue(any(msg.startswith(b"logout testuser") for msg in self.dummy_socket.sent))
    def test_delete_account(self):
        home.delete_account(self.dummy_socket, self.root, "testuser")
        self.assertTrue(any(msg.startswith(b"delete_acct testuser") for msg in self.dummy_socket.sent))

class TestScreensDeleteMessageLaunchHome(unittest.TestCase):
    def setUp(self):
        self.dummy_socket = DummySocketForScreens()
        self.root = DummyTk()
    def test_launch_home(self):
        delete_messages.launch_home(self.dummy_socket, self.root, "testuser")
        self.assertTrue(any(msg.startswith(b"refresh_home testuser") for msg in self.dummy_socket.sent))

###############################################################################
# Main block: run tests
###############################################################################

if __name__ == "__main__":
    unittest.main()
