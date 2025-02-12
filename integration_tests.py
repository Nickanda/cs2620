import os
import selectors
import types
import tempfile
import unittest
import tkinter as tk
from unittest.mock import patch
import hashlib

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
        self.save_patch = patch(
            "database_wrapper.save_database", lambda users, messages, settings: None
        )
        self.save_patch.start()

    def tearDown(self):
        self.save_patch.stop()

    def run_service(self, command_str, mask=selectors.EVENT_WRITE):
        """Helper: pre-populate outb with a command and call service_connection."""
        dummy_sock = DummySocket()
        data = types.SimpleNamespace(
            addr=("127.0.0.1", 12345), inb=b"", outb=command_str.encode("utf-8")
        )
        key = types.SimpleNamespace(fileobj=dummy_sock, data=data)
        main.service_connection(key, mask)
        return dummy_sock, data

    def test_create_invalid_username(self):
        # Non-alphanumeric username should return an error.
        sock, _ = self.run_service("create inv@lid somehash")
        self.assertTrue(
            any(b"error Username must be alphanumeric" in sent for sent in sock.sent)
        )

    def test_create_existing_username(self):
        # Create a user beforehand.
        main.users["testuser"] = {
            "password": hashlib.sha256("password".encode("utf-8")).hexdigest(),
            "logged_in": True,
            "addr": 1111,
        }
        sock, _ = self.run_service("create testuser somehash")
        self.assertTrue(
            any(b"error Username already exists" in sent for sent in sock.sent)
        )

    def test_create_empty_username(self):
        sock, _ = self.run_service("create  somehash")
        self.assertTrue(
            any(b"error Username must be alphanumeric" in sent for sent in sock.sent)
        )

    def test_create_empty_password(self):
        sock, _ = self.run_service("create validusername  ")
        self.assertTrue(
            any(b"error Password cannot be empty" in sent for sent in sock.sent)
        )

    def test_login_empty_username(self):
        sock, _ = self.run_service("login  password")
        self.assertTrue(
            any(b"error Username does not exist" in sent for sent in sock.sent)
        )

    def test_login_empty_password(self):
        main.users["validuser"] = {
            "password": hashlib.sha256("secret".encode("utf-8")).hexdigest(),
            "logged_in": False,
            "addr": 0,
        }
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
        self.assertTrue(
            any(b"error Username does not exist" in sent for sent in sock.sent)
        )

    def test_login_incorrect_password(self):
        hashed = hashlib.sha256("correct".encode("utf-8")).hexdigest()
        main.users["testuser"] = {"password": hashed, "logged_in": False, "addr": 0}
        sock, _ = self.run_service("login testuser wrong")
        self.assertTrue(any(b"error Incorrect password" in sent for sent in sock.sent))

    def test_login_already_logged_in(self):
        hashed = hashlib.sha256("secret".encode("utf-8")).hexdigest()
        main.users["testuser"] = {"password": hashed, "logged_in": True, "addr": 2222}
        sock, _ = self.run_service("login testuser secret")
        self.assertTrue(
            any(b"error User already logged in" in sent for sent in sock.sent)
        )

    def test_login_success(self):
        hashed = hashlib.sha256("secret".encode("utf-8")).hexdigest()
        main.users["testuser"] = {"password": hashed, "logged_in": False, "addr": 0}
        # Add an undelivered message for testuser.
        main.messages["undelivered"].append(
            {"id": 1, "sender": "other", "receiver": "testuser", "message": "Hello"}
        )
        sock, _ = self.run_service(f"login testuser {hashed}")
        self.assertTrue(any(b"login testuser 1" in sent for sent in sock.sent))
        self.assertTrue(main.users["testuser"]["logged_in"])

    def test_logout_nonexistent(self):
        sock, _ = self.run_service("logout unknown")
        self.assertTrue(
            any(b"error Username does not exist" in sent for sent in sock.sent)
        )

    def test_logout_success(self):
        main.users["testuser"] = {
            "password": hashlib.sha256("secret".encode("utf-8")).hexdigest(),
            "logged_in": True,
            "addr": 3333,
        }
        sock, _ = self.run_service("logout testuser")
        self.assertTrue(any(b"logout" in sent for sent in sock.sent))
        self.assertFalse(main.users["testuser"]["logged_in"])

    def test_search(self):
        # Setup a few users.
        main.users = {
            "alice": {"password": "x", "logged_in": False, "addr": 0},
            "bob": {"password": "x", "logged_in": False, "addr": 0},
            "charlie": {"password": "x", "logged_in": False, "addr": 0},
        }
        sock, _ = self.run_service("search a*")
        # Expected to match "alice"
        self.assertTrue(any(b"user_list alice" in sent for sent in sock.sent))

    def test_delete_acct(self):
        main.users = {
            "testuser": {
                "password": hashlib.sha256("secret".encode("utf-8")).hexdigest(),
                "logged_in": True,
                "addr": 4444,
            },
            "other": {"password": "x", "logged_in": False, "addr": 0},
        }
        # Add some messages that involve testuser.
        main.messages["delivered"] = [
            {"id": 1, "sender": "testuser", "receiver": "other", "message": "Hi"},
            {"id": 2, "sender": "other", "receiver": "testuser", "message": "Hello"},
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
        main.users = {
            "sender": {
                "password": hashlib.sha256("correct".encode("utf-8")).hexdigest(),
                "logged_in": True,
                "addr": 5555,
            }
        }
        sock, _ = self.run_service("send_msg sender unknown Hello")
        self.assertTrue(
            any(b"error Receiver does not exist" in sent for sent in sock.sent)
        )

    def test_send_msg_delivered(self):
        main.users = {
            "sender": {
                "password": hashlib.sha256("secret".encode("utf-8")).hexdigest(),
                "logged_in": True,
                "addr": 6666,
            },
            "receiver": {"password": "x", "logged_in": True, "addr": 7777},
        }
        initial_delivered = len(main.messages["delivered"])
        sock, _ = self.run_service("send_msg sender receiver Hi there")
        self.assertEqual(len(main.messages["delivered"]), initial_delivered + 1)
        self.assertTrue(any(b"refresh_home" in sent for sent in sock.sent))

    def test_send_msg_undelivered(self):
        main.users = {
            "sender": {
                "password": hashlib.sha256("secret".encode("utf-8")).hexdigest(),
                "logged_in": True,
                "addr": 8888,
            },
            "receiver": {"password": "x", "logged_in": False, "addr": 0},
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
            {"id": 3, "sender": "charlie", "receiver": "other", "message": "Msg3"},
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
            {"id": 12, "sender": "charlie", "receiver": "other", "message": "Msg12"},
        ]
        sock, _ = self.run_service("get_delivered testuser 1")
        self.assertTrue(any(b"messages" in sent for sent in sock.sent))

    def test_refresh_home(self):
        main.messages["undelivered"] = [
            {"id": 5, "sender": "x", "receiver": "testuser", "message": "Msg5"},
            {"id": 6, "sender": "y", "receiver": "testuser", "message": "Msg6"},
        ]
        sock, _ = self.run_service("refresh_home testuser")
        self.assertTrue(any(b"refresh_home 2" in sent for sent in sock.sent))

    def test_delete_msg(self):
        main.messages["delivered"] = [
            {"id": 20, "sender": "alice", "receiver": "testuser", "message": "Msg20"},
            {"id": 21, "sender": "bob", "receiver": "testuser", "message": "Msg21"},
            {"id": 22, "sender": "charlie", "receiver": "other", "message": "Msg22"},
        ]
        sock, _ = self.run_service("delete_msg testuser 20,21")
        for msg in main.messages["delivered"]:
            self.assertNotIn(msg["id"], [20, 21])
        self.assertTrue(any(b"refresh_home" in sent for sent in sock.sent))

    def test_delete_nonexistent_account(self):
        sock, _ = self.run_service("delete_acct nonexistent")
        self.assertTrue(
            any(b"error Account does not exist" in sent for sent in sock.sent)
        )

    def test_delete_account_with_messages(self):
        main.users["victim"] = {
            "password": hashlib.sha256("pass123".encode("utf-8")).hexdigest(),
            "logged_in": False,
            "addr": 0,
        }
        main.messages["undelivered"].append(
            {"id": 1, "sender": "other", "receiver": "victim", "message": "Message1"}
        )
        main.messages["delivered"].append(
            {"id": 2, "sender": "victim", "receiver": "other", "message": "Message2"}
        )
        sock, _ = self.run_service("delete_acct victim")
        self.assertNotIn("victim", main.users)
        self.assertFalse(
            any(msg["receiver"] == "victim" for msg in main.messages["undelivered"])
        )
        self.assertFalse(
            any(msg["sender"] == "victim" for msg in main.messages["delivered"])
        )
        self.assertTrue(any(b"logout" in sent for sent in sock.sent))

    def test_create_username_too_long(self):
        long_username = "u" * 64  # 64-char username
        command = f"create {long_username} somepasswordhash"
        sock, _ = self.run_service(command)
        self.assertIn(
            long_username,
            main.users,
            "The user should still be created (no explicit code blocking).",
        )
        self.assertTrue(any(b"login" in sent for sent in sock.sent))

    def test_create_password_too_long(self):
        long_password = "p" * 128
        command = f"create shortusername {long_password}"
        sock, _ = self.run_service(command)
        self.assertIn("shortusername", main.users)
        self.assertTrue(any(b"login shortusername 0" in sent for sent in sock.sent))

    def test_send_msg_empty_message_body(self):
        main.users = {
            "sender": {
                "password": hashlib.sha256("secret".encode("utf-8")).hexdigest(),
                "logged_in": True,
                "addr": 9999,
            },
            "receiver": {"password": "x", "logged_in": True, "addr": 10000},
        }
        sock, _ = self.run_service("send_msg sender receiver ")
        self.assertEqual(
            len(main.messages["delivered"]),
            1,
            "Even empty messages are delivered under current logic.",
        )
        self.assertTrue(any(b"refresh_home" in sent for sent in sock.sent))

    def test_login_with_long_password(self):
        hashed = hashlib.sha256("secret".encode("utf-8")).hexdigest()
        main.users["longpass"] = {"password": hashed, "logged_in": False, "addr": 0}
        long_wrong_password = "x" * 200
        sock, _ = self.run_service(f"login longpass {long_wrong_password}")
        self.assertTrue(any(b"error Incorrect password" in sent for sent in sock.sent))

    def test_get_undelivered_zero_requested(self):
        main.messages["undelivered"] = [
            {"id": 1, "sender": "a", "receiver": "user", "message": "Hello"}
        ]
        sock, _ = self.run_service("get_undelivered user 0")
        self.assertTrue(
            any(b"messages " in sent for sent in sock.sent),
            "Should respond with 'messages' command, but no messages returned.",
        )
        self.assertEqual(len(main.messages["undelivered"]), 1)

    ############################################################################
    ############################################################################
    #! FLAGGING THIS ONE SINCE THIS PASSES HOW ARE WE JOINING THESE THINGS
    def test_get_delivered_more_than_exist(self):
        main.messages["delivered"] = [
            {"id": 10, "sender": "alice", "receiver": "testuser", "message": "Msg10"},
            {"id": 11, "sender": "bob", "receiver": "testuser", "message": "Msg11"},
        ]
        sock, _ = self.run_service("get_delivered testuser 5")
        self.assertTrue(
            any(
                b"messages 10_alice_Msg10\x0011_bob_Msg11" in sent for sent in sock.sent
            ),
            "Should deliver both messages since we asked for 5.",
        )

    #! FLAGGING THIS ONE SINCE THIS PASSES HOW ARE WE JOINING THESE THINGS
    ############################################################################
    ############################################################################

    def test_search_no_match(self):
        main.users = {
            "alice": {"password": "x", "logged_in": False, "addr": 0},
            "bob": {"password": "x", "logged_in": False, "addr": 0},
        }
        sock, _ = self.run_service("search char*")
        self.assertTrue(any(b"user_list" in sent for sent in sock.sent))
        for sent in sock.sent:
            if b"user_list" in sent:
                self.assertEqual(
                    sent,
                    b"user_list ",
                    "No users matched, so it should be 'user_list ' with nothing else.",
                )


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
        self.test_dir.cleanup()
        database_wrapper.users_database_path = self.orig_users_path
        database_wrapper.messages_database_path = self.orig_messages_path
        database_wrapper.settings_database_path = self.orig_settings_path

    def test_load_database_creates_files(self):
        # Remove files if they exist.
        for path in [
            database_wrapper.users_database_path,
            database_wrapper.messages_database_path,
            database_wrapper.settings_database_path,
        ]:
            if os.path.exists(path):
                os.remove(path)
        users, messages, settings = database_wrapper.load_database()
        self.assertEqual(users, {})
        self.assertEqual(messages, {"undelivered": [], "delivered": []})
        self.assertEqual(settings, {"counter": 0})

    def test_save_and_load_database(self):
        users = {"user1": {"password": "hash", "logged_in": False, "addr": 0}}
        messages = {
            "undelivered": [
                {"id": 1, "sender": "user2", "receiver": "user1", "message": "Hi"}
            ],
            "delivered": [],
        }
        settings = {"counter": 1}
        database_wrapper.save_database(users, messages, settings)
        loaded_users, loaded_messages, loaded_settings = (
            database_wrapper.load_database()
        )
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

    def test_save_database_overwrites_files(self):
        # Write old data
        database_wrapper.save_database(
            {"olduser": {}}, {"undelivered": [], "delivered": []}, {"counter": 99}
        )
        # Overwrite with new data
        database_wrapper.save_database(
            {"newuser": {"password": "p"}},
            {"undelivered": [], "delivered": []},
            {"counter": 0},
        )
        loaded_users, loaded_messages, loaded_settings = (
            database_wrapper.load_database()
        )
        self.assertIn("newuser", loaded_users)
        self.assertNotIn(
            "olduser", loaded_users, "Old data should have been overwritten."
        )


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
        with patch("screens.signup.messagebox.showerror") as mock_showerror:
            signup_screen.create_user(
                self.dummy_socket, self.root, username_var, password_var
            )
            # Expect a message starting with "create testuser "
            self.assertTrue(
                any(
                    msg.startswith(b"create testuser ")
                    for msg in self.dummy_socket.sent
                )
            )
            self.assertTrue(self.root.destroy_called)
            mock_showerror.assert_not_called()

    def test_create_user_invalid_username(self):
        username_var = tk.StringVar(self.tk_root, value="test*user")
        password_var = tk.StringVar(self.tk_root, value="secret")
        with patch("screens.signup.messagebox.showerror") as mock_showerror:
            signup_screen.create_user(
                self.dummy_socket, self.root, username_var, password_var
            )
            mock_showerror.assert_called_once_with(
                "Error", "Username must be alphanumeric"
            )

    def test_create_user_blank_password(self):
        username_var = tk.StringVar(self.tk_root, value="validuser")
        password_var = tk.StringVar(self.tk_root, value="")
        with patch("screens.signup.messagebox.showerror") as mock_showerror:
            signup_screen.create_user(
                self.dummy_socket, self.root, username_var, password_var
            )
            mock_showerror.assert_called_once_with("Error", "All fields are required")
            self.assertFalse(self.root.destroy_called)


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
        hashed_password = hashlib.sha256(password_var.get().encode("utf-8")).hexdigest()
        with patch("screens.login.messagebox.showerror") as mock_showerror:
            login_screen.login(self.dummy_socket, self.root, username_var, password_var)
            self.assertTrue(
                any(
                    msg.startswith(f"login testuser {hashed_password}".encode("utf-8"))
                    for msg in self.dummy_socket.sent
                )
            )
            self.assertTrue(self.root.destroy_called)
            mock_showerror.assert_not_called()

    def test_login_invalid_username(self):
        username_var = tk.StringVar(self.tk_root, value="test*user")
        password_var = tk.StringVar(self.tk_root, value="secret")
        with patch("screens.login.messagebox.showerror") as mock_showerror:
            login_screen.login(self.dummy_socket, self.root, username_var, password_var)
            mock_showerror.assert_called_once_with(
                "Error", "Username must be alphanumeric"
            )

    def test_login_blank_username(self):
        username_var = tk.StringVar(self.tk_root, value="")
        password_var = tk.StringVar(self.tk_root, value="password")
        with patch("screens.login.messagebox.showerror") as mock_showerror:
            login_screen.login(self.dummy_socket, self.root, username_var, password_var)
            mock_showerror.assert_called_once_with("Error", "All fields are required")

    def test_login_blank_password(self):
        username_var = tk.StringVar(self.tk_root, value="validuser")
        password_var = tk.StringVar(self.tk_root, value="")
        with patch("screens.login.messagebox.showerror") as mock_showerror:
            login_screen.login(self.dummy_socket, self.root, username_var, password_var)
            mock_showerror.assert_called_once_with("Error", "All fields are required")
            self.assertFalse(self.root.destroy_called)


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
        with patch("screens.send_message.messagebox.showerror") as mock_showerror:
            send_message_screen.send_message(
                self.dummy_socket, self.root, recipient_var, text_widget, "sender"
            )
            self.assertTrue(
                any(
                    msg.startswith(b"send_msg sender receiver Hello there")
                    for msg in self.dummy_socket.sent
                )
            )
            self.assertTrue(self.root.destroy_called)
            mock_showerror.assert_not_called()

    def test_send_message_invalid_recipient(self):
        recipient_var = tk.StringVar(self.tk_root, value="receiver!")
        text_widget = tk.Text(self.tk_root)
        text_widget.insert("1.0", "Hello there")
        with patch("screens.send_message.messagebox.showerror") as mock_showerror:
            send_message_screen.send_message(
                self.dummy_socket, self.root, recipient_var, text_widget, "sender"
            )
            mock_showerror.assert_called_once_with(
                "Error", "Username must be alphanumeric"
            )

    def test_send_message_blank_recipient(self):
        recipient_var = tk.StringVar(self.tk_root, value="")
        text_widget = tk.Text(self.tk_root)
        text_widget.insert("1.0", "Hello")
        with patch("screens.send_message.messagebox.showerror") as mock_showerror:
            send_message_screen.send_message(
                self.dummy_socket, self.root, recipient_var, text_widget, "sender"
            )
            mock_showerror.assert_called_once_with("Error", "All fields are required")

    def test_send_message_blank_content(self):
        recipient_var = tk.StringVar(self.tk_root, value="validrecipient")
        text_widget = tk.Text(self.tk_root)
        # No text inserted => blank
        with patch("screens.send_message.messagebox.showerror") as mock_showerror:
            send_message_screen.send_message(
                self.dummy_socket, self.root, recipient_var, text_widget, "sender"
            )
            mock_showerror.assert_called_once_with("Error", "All fields are required")
            self.assertFalse(self.root.destroy_called)


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
        with patch("screens.delete_messages.messagebox.showerror") as mock_showerror:
            delete_messages.delete_message(
                self.dummy_socket, self.root, delete_ids_var, "testuser"
            )
            self.assertTrue(
                any(
                    msg.startswith(b"delete_msg testuser 1,2,3")
                    for msg in self.dummy_socket.sent
                )
            )
            self.assertTrue(self.root.destroy_called)
            mock_showerror.assert_not_called()

    def test_delete_message_invalid_ids(self):
        delete_ids_var = tk.StringVar(self.tk_root, value="1, 2,3")  # contains a space
        with patch("screens.delete_messages.messagebox.showerror") as mock_showerror:
            delete_messages.delete_message(
                self.dummy_socket, self.root, delete_ids_var, "testuser"
            )
            mock_showerror.assert_called_once_with(
                "Error", "Delete IDs must be alphanumeric comma-separated list"
            )

    def test_delete_message_invalid_input(self):
        delete_ids_var = tk.StringVar(self.tk_root, value="bad input!")
        with patch("screens.delete_messages.messagebox.showerror") as mock_showerror:
            delete_messages.delete_message(
                self.dummy_socket, self.root, delete_ids_var, "user"
            )
            mock_showerror.assert_called_once_with(
                "Error", "Delete IDs must be alphanumeric comma-separated list"
            )

    def test_delete_message_blank_input(self):
        delete_ids_var = tk.StringVar(self.tk_root, value="")
        with patch("screens.delete_messages.messagebox.showerror") as mock_showerror:
            delete_messages.delete_message(
                self.dummy_socket, self.root, delete_ids_var, "testuser"
            )
            mock_showerror.assert_called_once_with("Error", "All fields are required")
            self.assertFalse(self.root.destroy_called)


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
        with patch("screens.user_list.messagebox.showerror") as mock_showerror:
            user_list_screen.search(self.dummy_socket, self.root, search_var)
            self.assertTrue(
                any(msg.startswith(b"search alice*") for msg in self.dummy_socket.sent)
            )
            self.assertTrue(self.root.destroy_called)
            mock_showerror.assert_not_called()

    def test_search_invalid(self):
        search_var = tk.StringVar(self.tk_root, value="alice#")
        with patch("screens.user_list.messagebox.showerror") as mock_showerror:
            user_list_screen.search(self.dummy_socket, self.root, search_var)
            mock_showerror.assert_called_once_with(
                "Error", "Search characters must be alphanumeric or *"
            )

    def test_search_blank(self):
        search_var = tk.StringVar(self.tk_root, value="")
        with patch("screens.user_list.messagebox.showerror") as mock_showerror:
            user_list_screen.search(self.dummy_socket, self.root, search_var)
            mock_showerror.assert_called_once_with("Error", "All fields are required")

    def test_search_just_star(self):
        """Test searching with '*' only should return all users if any exist."""
        search_var = tk.StringVar(self.tk_root, value="*")
        with patch("screens.user_list.messagebox.showerror") as mock_showerror:
            user_list_screen.search(self.dummy_socket, self.root, search_var)
            self.assertTrue(
                any(msg.startswith(b"search *") for msg in self.dummy_socket.sent)
            )
            self.assertTrue(self.root.destroy_called)
            mock_showerror.assert_not_called()


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
        with patch("screens.messages.messagebox.showerror") as mock_showerror:
            messages_screen.get_undelivered_messages(
                self.dummy_socket, self.root, num_messages_var, "testuser"
            )
            self.assertTrue(
                any(
                    msg.startswith(b"get_undelivered testuser 2")
                    for msg in self.dummy_socket.sent
                )
            )
            self.assertTrue(self.root.destroy_called)
            mock_showerror.assert_not_called()

    def test_get_undelivered_messages_zero(self):
        num_messages_var = tk.IntVar(self.tk_root, value=0)
        with patch("screens.messages.messagebox.showerror") as mock_showerror:
            messages_screen.get_undelivered_messages(
                self.dummy_socket, self.root, num_messages_var, "testuser"
            )
            mock_showerror.assert_called_once_with(
                "Error", "Number of messages must be greater than 0"
            )

    def test_get_delivered_messages_valid(self):
        num_messages_var = tk.IntVar(self.tk_root, value=3)
        with patch("screens.messages.messagebox.showerror") as mock_showerror:
            messages_screen.get_delivered_messages(
                self.dummy_socket, self.root, num_messages_var, "testuser"
            )
            self.assertTrue(
                any(
                    msg.startswith(b"get_delivered testuser 3")
                    for msg in self.dummy_socket.sent
                )
            )
            self.assertTrue(self.root.destroy_called)
            mock_showerror.assert_not_called()

    def test_get_delivered_negative_number(self):
        """Try passing a negative number of messages to get_delivered and check for error handling."""
        num_messages_var = tk.IntVar(self.tk_root, value=-1)
        with patch("screens.messages.messagebox.showerror") as mock_showerror:
            messages_screen.get_delivered_messages(
                self.dummy_socket, self.root, num_messages_var, "testuser"
            )
            mock_showerror.assert_called_once_with(
                "Error", "Number of messages must be greater than 0"
            )
            self.assertFalse(self.root.destroy_called)

    def test_get_undelivered_negative_number(self):
        """Try passing a negative number of messages to get_undelivered and check for error handling."""
        num_messages_var = tk.IntVar(self.tk_root, value=-5)
        with patch("screens.messages.messagebox.showerror") as mock_showerror:
            messages_screen.get_undelivered_messages(
                self.dummy_socket, self.root, num_messages_var, "testuser"
            )
            mock_showerror.assert_called_once_with(
                "Error", "Number of messages must be greater than 0"
            )
            self.assertFalse(self.root.destroy_called)


class TestScreensHome(unittest.TestCase):
    def setUp(self):
        self.dummy_socket = DummySocketForScreens()
        self.root = DummyTk()

    def test_open_read_messages(self):
        with patch("screens.home.screens.messages.launch_window") as mock_launch:
            home.open_read_messages(self.dummy_socket, self.root, "testuser")
            mock_launch.assert_called_once_with(self.dummy_socket, [], "testuser")

    def test_open_send_message(self):
        with patch("screens.home.screens.send_message.launch_window") as mock_launch:
            home.open_send_message(self.dummy_socket, self.root, "testuser")
            mock_launch.assert_called_once_with(self.dummy_socket, "testuser")

    def test_open_delete_messages(self):
        with patch("screens.home.screens.delete_messages.launch_window") as mock_launch:
            home.open_delete_messages(self.dummy_socket, self.root, "testuser")
            mock_launch.assert_called_once_with(self.dummy_socket, "testuser")

    def test_open_user_list(self):
        with patch("screens.home.screens.user_list.launch_window") as mock_launch:
            home.open_user_list(self.dummy_socket, self.root, "testuser")
            mock_launch.assert_called_once_with(self.dummy_socket, [], "testuser")

    def test_logout(self):
        home.logout(self.dummy_socket, self.root, "testuser")
        self.assertTrue(
            any(msg.startswith(b"logout testuser") for msg in self.dummy_socket.sent)
        )

    def test_delete_account(self):
        home.delete_account(self.dummy_socket, self.root, "testuser")
        self.assertTrue(
            any(
                msg.startswith(b"delete_acct testuser")
                for msg in self.dummy_socket.sent
            )
        )


class TestScreensDeleteMessageLaunchHome(unittest.TestCase):
    def setUp(self):
        self.dummy_socket = DummySocketForScreens()
        self.root = DummyTk()

    def test_launch_home(self):
        delete_messages.launch_home(self.dummy_socket, self.root, "testuser")
        self.assertTrue(
            any(
                msg.startswith(b"refresh_home testuser")
                for msg in self.dummy_socket.sent
            )
        )


# ----------------------------- ADDITIONAL TESTS HERE -----------------------------
# Below are newly added tests that further expand coverage for edge cases,
# error handling, and normal functionality. The existing tests above remain unchanged.


class TestMainServiceConnectionAdditional(unittest.TestCase):
    def setUp(self):
        # Reset globals used by main.py
        main.users = {}
        main.messages = {"undelivered": [], "delivered": []}
        main.settings = {"counter": 0}
        # Patch database saving
        self.save_patch = patch(
            "database_wrapper.save_database", lambda users, messages, settings: None
        )
        self.save_patch.start()

    def tearDown(self):
        self.save_patch.stop()

    def run_service(self, command_str, mask=selectors.EVENT_WRITE):
        """Helper for sending commands to the main.service_connection."""
        dummy_sock = DummySocket()
        data = types.SimpleNamespace(
            addr=("127.0.0.1", 10000), inb=b"", outb=command_str.encode("utf-8")
        )
        key = types.SimpleNamespace(fileobj=dummy_sock, data=data)
        main.service_connection(key, mask)
        return dummy_sock, data

    def test_create_numeric_only_username(self):
        sock, _ = self.run_service("create 12345 passwordhash")
        self.assertIn("12345", main.users)
        self.assertTrue(main.users["12345"]["logged_in"])
        self.assertTrue(any(b"login 12345 0" in s for s in sock.sent))

    def test_login_with_trailing_spaces(self):
        # Create user first
        hashed = hashlib.sha256("secret123".encode("utf-8")).hexdigest()
        main.users["username"] = {"password": hashed, "logged_in": False, "addr": 0}
        sock, _ = self.run_service(f"login username {hashed}   ")
        self.assertTrue(
            any(b"login username 0" in s for s in sock.sent),
            "Login should succeed despite trailing spaces.",
        )

    def test_send_message_sender_not_logged_in(self):
        # We have a user in the system, but they're not logged in.
        main.users["sender"] = {
            "password": hashlib.sha256("pass".encode("utf-8")).hexdigest(),
            "logged_in": False,
            "addr": 0,
        }
        main.users["receiver"] = {"password": "x", "logged_in": True, "addr": 1234}
        sock, _ = self.run_service("send_msg sender receiver HelloWhileLoggedOut")
        # Code doesn't currently explicitly block a logged-out sender from sending.
        # Let's see what happens: it processes it anyway.
        # There's no direct check for "logged_in" in `send_msg` logic.
        # So it should go through as "undelivered" or "delivered" (since receiver is logged in).
        # Actually, since receiver is logged in, it's added to delivered.
        self.assertEqual(
            len(main.messages["delivered"]),
            1,
            "Message was delivered even though the sender wasn't logged in.",
        )
        # This tests a possible system gap; we confirm the code's actual behavior.
        self.assertTrue(any(b"refresh_home" in s for s in sock.sent))

    def test_delete_message_not_owned_by_user(self):
        # Create delivered messages for multiple users
        main.messages["delivered"] = [
            {"id": 100, "sender": "alice", "receiver": "bob", "message": "Hello Bob"},
            {
                "id": 101,
                "sender": "charlie",
                "receiver": "testuser",
                "message": "Hello Testuser",
            },
        ]
        # Attempt to delete 100,101 as "testuser"
        sock, _ = self.run_service("delete_msg testuser 100,101")
        # user "testuser" can only delete messages where testuser is the receiver, which includes msg id=101.
        # But msg id=100 is bob's. That should remain. The code only checks `(msg["receiver"] == current_user)`.
        # So 101 should be deleted, 100 should remain.
        self.assertFalse(
            any(m["id"] == 101 for m in main.messages["delivered"]),
            "Message 101 should be deleted.",
        )
        self.assertTrue(
            any(m["id"] == 100 for m in main.messages["delivered"]),
            "Message 100 should remain.",
        )
        self.assertTrue(any(b"refresh_home" in s for s in sock.sent))

    def test_send_message_with_special_characters_in_body(self):
        main.users = {
            "sender": {
                "password": hashlib.sha256("secret".encode("utf-8")).hexdigest(),
                "logged_in": True,
                "addr": 20000,
            },
            "receiver": {"password": "x", "logged_in": True, "addr": 30000},
        }
        sock, _ = self.run_service("send_msg sender receiver Hello!@#$%^&*()")
        self.assertEqual(len(main.messages["delivered"]), 1)
        self.assertIn("Hello!@#$%^&*()", main.messages["delivered"][0]["message"])
        self.assertTrue(any(b"refresh_home" in s for s in sock.sent))

    def test_search_extreme_wildcard(self):
        main.users = {
            "alice": {"password": "x", "logged_in": False, "addr": 0},
            "alice123": {"password": "x", "logged_in": False, "addr": 0},
            "xyz": {"password": "x", "logged_in": False, "addr": 0},
        }
        # '*' wildcard should return all, no matter how many
        sock, _ = self.run_service(
            "search ****************************************************************"
        )
        # We expect the server's fnmatch logic to consider that as a big wildcard too.
        # Should match everything.
        self.assertTrue(
            any(
                b"user_list alice alice123 xyz" in s
                or b"user_list xyz alice alice123" in s
                for s in sock.sent
            )
        )

    def test_get_undelivered_nonexistent_user(self):
        # If a user not in `main.users` tries to get undelivered
        sock, _ = self.run_service("get_undelivered ghost 2")
        # The code does not check if the user actually exists, so it won't raise an error
        # but also won't deliver anything. It simply filters on the "receiver" field.
        # Make sure there's no crash or weird error:
        self.assertTrue(
            any(b"error No undelivered messages" in s for s in sock.sent),
            "Should respond with an error.",
        )

    def test_get_delivered_for_nonexistent_user(self):
        # If "ghost" doesn't exist in main.users, but user calls get_delivered ghost 2
        # The system doesn't specifically verify the user. It filters messages for the receiver=ghost.
        # So if none exist, it returns an empty message set.
        sock, _ = self.run_service("get_delivered ghost 2")
        self.assertTrue(
            any(b"error No delivered messages" in s for s in sock.sent),
            "Should respond with an error.",
        )

    def test_create_user_with_numeric_password(self):
        # Nothing in code forbids numeric passwords
        sock, _ = self.run_service("create userwithnumericpass 1234567890")
        self.assertIn("userwithnumericpass", main.users)
        self.assertTrue(any(b"login userwithnumericpass 0" in s for s in sock.sent))

    def test_delete_acct_case_sensitivity(self):
        # Suppose we treat usernames case-sensitively (the code does not do any .lower()).
        main.users["CaseUser"] = {
            "password": hashlib.sha256("p".encode("utf-8")).hexdigest(),
            "logged_in": True,
            "addr": 4444,
        }
        sock, _ = self.run_service("delete_acct caseuser")
        # "caseuser" != "CaseUser", so we expect "error Account does not exist"
        self.assertTrue(
            any(b"error Account does not exist" in s for s in sock.sent),
            "No case-insensitive match, so it should yield error.",
        )


class TestScreensAdditional(unittest.TestCase):
    def setUp(self):
        self.dummy_socket = DummySocketForScreens()
        self.root = DummyTk()
        # For StringVar usage
        self.tk_root = tk.Tk()
        self.tk_root.withdraw()

    def tearDown(self):
        self.tk_root.destroy()

    def test_signup_numeric_username(self):
        username_var = tk.StringVar(self.tk_root, value="1234")
        password_var = tk.StringVar(self.tk_root, value="somepass")
        with patch("screens.signup.messagebox.showerror") as mock_showerror:
            signup_screen.create_user(
                self.dummy_socket, self.root, username_var, password_var
            )
            self.assertTrue(
                any(msg.startswith(b"create 1234 ") for msg in self.dummy_socket.sent)
            )
            self.assertTrue(self.root.destroy_called)
            mock_showerror.assert_not_called()

    def test_login_spaces_in_password(self):
        username_var = tk.StringVar(self.tk_root, value="userwithspaces")
        password_var = tk.StringVar(self.tk_root, value="secret with spaces")
        hashed_password = hashlib.sha256(password_var.get().encode("utf-8")).hexdigest()
        with patch("screens.login.messagebox.showerror") as mock_showerror:
            login_screen.login(self.dummy_socket, self.root, username_var, password_var)
            # Expect "login userwithspaces secret with spaces"
            self.assertTrue(
                any(
                    msg.startswith(
                        f"login userwithspaces {hashed_password}".encode("utf-8")
                    )
                    for msg in self.dummy_socket.sent
                )
            )
            self.assertTrue(self.root.destroy_called)
            mock_showerror.assert_not_called()

    def test_send_message_special_characters(self):
        recipient_var = tk.StringVar(self.tk_root, value="receiver")
        text_widget = tk.Text(self.tk_root)
        text_widget.insert("1.0", 'Special chars: ~!@#$%^&*()_+{}|:"<>?')
        with patch("screens.send_message.messagebox.showerror") as mock_showerror:
            send_message_screen.send_message(
                self.dummy_socket, self.root, recipient_var, text_widget, "sender123"
            )
            # Check if the message got sent
            self.assertTrue(
                any(
                    b'send_msg sender123 receiver Special chars: ~!@#$%^&*()_+{}|:"<>?'
                    in msg
                    for msg in self.dummy_socket.sent
                )
            )
            self.assertTrue(self.root.destroy_called)
            mock_showerror.assert_not_called()

    def test_delete_messages_non_alphanumeric_comma_list(self):
        delete_ids_var = tk.StringVar(self.tk_root, value="msg1,msg2!")
        with patch("screens.delete_messages.messagebox.showerror") as mock_showerror:
            delete_messages.delete_message(
                self.dummy_socket, self.root, delete_ids_var, "testuser"
            )
            mock_showerror.assert_called_once_with(
                "Error", "Delete IDs must be alphanumeric comma-separated list"
            )

    def test_user_list_search_asterisk_in_middle(self):
        search_var = tk.StringVar(self.tk_root, value="ab*cd")
        with patch("screens.user_list.messagebox.showerror") as mock_showerror:
            user_list_screen.search(self.dummy_socket, self.root, search_var)
            # We want to ensure it's accepted as an alphanumeric plus '*'
            # "ab*cd" is valid based on code (it will do fnmatch on that).
            self.assertTrue(
                any(msg.startswith(b"search ab*cd") for msg in self.dummy_socket.sent)
            )
            self.assertTrue(self.root.destroy_called)
            mock_showerror.assert_not_called()


if __name__ == "__main__":
    unittest.main()
