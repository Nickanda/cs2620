import unittest
import json
import types
from unittest.mock import patch

# Import the modules to be tested.
import server
import database_wrapper
import client_json

# --- Helper Classes and Functions ---


# Dummy socket to capture sent data.
class DummySocket:
    def __init__(self):
        self.sent_data = []

    def send(self, data):
        self.sent_data.append(data)
        return len(data)


# Helper function to create a dummy data object (simulating types.SimpleNamespace).
def create_dummy_data(addr=("127.0.0.1", 12345), outb=b""):
    return types.SimpleNamespace(addr=addr, outb=outb)


# Dummy internal communicator to override network updates.
class DummyInternalCommunicator:
    def __init__(self):
        self.last_update = None

    def distribute_update(self, update):
        self.last_update = update


# --- Unit Tests for FaultTolerantServer (server.py) ---
class TestFaultTolerantServer(unittest.TestCase):
    def setUp(self):
        # Patch load_database to avoid file I/O.
        self.dummy_users = {}
        self.dummy_messages = {"undelivered": [], "delivered": []}
        self.dummy_settings = {
            "counter": 0,
            "host": "127.0.0.1",
            "port": 54400,
            "host_json": "127.0.0.1",
            "port_json": 54444,
        }
        patcher = patch(
            "database_wrapper.load_database",
            return_value=(self.dummy_users, self.dummy_messages, self.dummy_settings),
        )
        self.addCleanup(patcher.stop)
        self.mock_load_database = patcher.start()

        # Patch save_database to do nothing.
        patcher2 = patch("database_wrapper.save_database", return_value=None)
        self.addCleanup(patcher2.stop)
        self.mock_save_database = patcher2.start()

        # Create an instance of FaultTolerantServer.
        self.server_instance = server.FaultTolerantServer(
            id=0,
            host="localhost",
            port=50000,
            current_starting_port=60000,
            internal_other_servers=["localhost"],
            internal_other_ports=[60000],
            internal_max_ports=[10],
        )
        # Replace internal communicator with a dummy.
        self.server_instance.internal_communicator = DummyInternalCommunicator()

    def test_parse_json_data_valid(self):
        # Prepare a valid JSON command.
        command_obj = {"version": 0, "command": "test", "data": {"key": "value"}}
        data_str = json.dumps(command_obj)
        dummy_data = create_dummy_data(outb=data_str.encode("utf-8"))
        dummy_sock = DummySocket()
        command, command_data, data, data_length = self.server_instance.parse_json_data(
            dummy_sock, dummy_data
        )
        self.assertEqual(command, "test")
        self.assertEqual(command_data, {"key": "value"})
        self.assertEqual(data_length, len(data_str))

    def test_create_account_valid(self):
        # Test valid account creation.
        command_obj = {
            "version": 0,
            "command": "create",
            "data": {"username": "user1", "password": "pass1"},
        }
        data_str = json.dumps(command_obj)
        dummy_data = create_dummy_data(
            addr=("127.0.0.1", 12345), outb=data_str.encode("utf-8")
        )
        dummy_sock = DummySocket()

        self.server_instance.create_account(
            dummy_sock, dummy_data, internal_change=False
        )

        # Verify that the user is added.
        self.assertIn("user1", self.server_instance.database["users"])
        # Check that a response message was sent.
        self.assertTrue(len(dummy_sock.sent_data) > 0)
        response = json.loads(dummy_sock.sent_data[0].decode("utf-8"))
        self.assertEqual(response["command"], "login")

    def test_create_account_invalid_username(self):
        # Test account creation with a non-alphanumeric username.
        command_obj = {
            "version": 0,
            "command": "create",
            "data": {"username": "user!", "password": "pass1"},
        }
        data_str = json.dumps(command_obj)
        dummy_data = create_dummy_data(
            addr=("127.0.0.1", 12345), outb=data_str.encode("utf-8")
        )
        dummy_sock = DummySocket()

        self.server_instance.create_account(
            dummy_sock, dummy_data, internal_change=False
        )
        # Verify that an error response was sent.
        self.assertTrue(len(dummy_sock.sent_data) > 0)
        response = json.loads(dummy_sock.sent_data[0].decode("utf-8"))
        self.assertEqual(response["command"], "error")

    def test_login_nonexistent_user(self):
        # Test logging in a user that does not exist.
        command_obj = {
            "version": 0,
            "command": "login",
            "data": {"username": "nonexistent", "password": "pass"},
        }
        data_str = json.dumps(command_obj)
        dummy_data = create_dummy_data(
            addr=("127.0.0.1", 12345), outb=data_str.encode("utf-8")
        )
        dummy_sock = DummySocket()

        self.server_instance.login(dummy_sock, dummy_data, internal_change=False)
        self.assertTrue(len(dummy_sock.sent_data) > 0)
        response = json.loads(dummy_sock.sent_data[0].decode("utf-8"))
        self.assertEqual(response["command"], "error")

    def test_get_new_messages(self):
        # Add undelivered messages and verify the count.
        self.server_instance.database["messages"]["undelivered"] = [
            {"receiver": "user1", "id": 1, "sender": "user2", "message": "Hello"},
            {"receiver": "user1", "id": 2, "sender": "user3", "message": "Hi"},
            {"receiver": "user2", "id": 3, "sender": "user1", "message": "Hey"},
        ]
        count = self.server_instance.get_new_messages("user1")
        self.assertEqual(count, 2)

    def test_deliver_message_logged_in(self):
        # Set up users where the recipient is logged in.
        self.server_instance.database["users"] = {
            "user1": {
                "password": "pass1",
                "logged_in": True,
                "addr": "127.0.0.1:12345",
            },
            "user2": {
                "password": "pass2",
                "logged_in": True,
                "addr": "127.0.0.1:54321",
            },
        }
        command_obj = {
            "version": 0,
            "command": "send_msg",
            "data": {"sender": "user1", "recipient": "user2", "message": "Hello"},
        }
        data_str = json.dumps(command_obj)
        dummy_data = create_dummy_data(
            addr=("127.0.0.1", 12345), outb=data_str.encode("utf-8")
        )
        dummy_sock = DummySocket()

        self.server_instance.deliver_message(
            dummy_sock, dummy_data, internal_change=False
        )
        delivered = self.server_instance.database["messages"]["delivered"]
        self.assertEqual(len(delivered), 1)
        self.assertEqual(delivered[0]["message"], "Hello")

    def test_deliver_message_not_logged_in(self):
        # Set up users where the recipient is not logged in.
        self.server_instance.database["users"] = {
            "user1": {
                "password": "pass1",
                "logged_in": True,
                "addr": "127.0.0.1:12345",
            },
            "user2": {
                "password": "pass2",
                "logged_in": False,
                "addr": "127.0.0.1:54321",
            },
        }
        command_obj = {
            "version": 0,
            "command": "send_msg",
            "data": {"sender": "user1", "recipient": "user2", "message": "Hello"},
        }
        data_str = json.dumps(command_obj)
        dummy_data = create_dummy_data(
            addr=("127.0.0.1", 12345), outb=data_str.encode("utf-8")
        )
        dummy_sock = DummySocket()

        self.server_instance.deliver_message(
            dummy_sock, dummy_data, internal_change=False
        )
        undelivered = self.server_instance.database["messages"]["undelivered"]
        self.assertEqual(len(undelivered), 1)
        self.assertEqual(undelivered[0]["message"], "Hello")


# --- Unit Tests for the Database Wrapper (database_wrapper.py) ---
class TestDatabaseWrapper(unittest.TestCase):
    def setUp(self):
        # Use a test VM ID and reset the database.
        self.test_vm_id = "test_vm"
        database_wrapper.reset_database(self.test_vm_id)

    def tearDown(self):
        # Clean up files created during the tests.
        import os

        for func in [
            database_wrapper.users_database_path,
            database_wrapper.messages_database_path,
            database_wrapper.settings_database_path,
        ]:
            path = func(self.test_vm_id)
            if os.path.exists(path):
                os.remove(path)
        if os.path.exists("database") and not os.listdir("database"):
            os.rmdir("database")

    def test_reset_database(self):
        users, messages, settings = database_wrapper.reset_database(self.test_vm_id)
        self.assertEqual(users, {})
        self.assertEqual(messages, {"undelivered": [], "delivered": []})
        self.assertEqual(settings["counter"], 0)

    def test_save_and_load_database(self):
        dummy_users = {
            "user1": {"password": "pass", "logged_in": True, "addr": "127.0.0.1:12345"}
        }
        dummy_messages = {
            "undelivered": [
                {"id": 1, "sender": "user2", "receiver": "user1", "message": "Hi"}
            ],
            "delivered": [],
        }
        dummy_settings = {
            "counter": 1,
            "host": "127.0.0.1",
            "port": 54400,
            "host_json": "127.0.0.1",
            "port_json": 54444,
        }
        database_wrapper.save_database(
            self.test_vm_id, dummy_users, dummy_messages, dummy_settings
        )
        loaded_users, loaded_messages, loaded_settings = database_wrapper.load_database(
            self.test_vm_id
        )
        self.assertEqual(loaded_users, dummy_users)
        self.assertEqual(loaded_messages, dummy_messages)
        self.assertEqual(loaded_settings, dummy_settings)


# --- Unit Test for Client JSON Argument Parsing (client_json.py) ---
class TestClientJson(unittest.TestCase):
    def test_parse_arguments_defaults(self):
        import sys

        test_args = ["client_json.py"]
        sys.argv = test_args
        args = client_json.parse_arguments()
        self.assertEqual(args.hosts, "localhost")
        self.assertEqual(args.ports, "50000")
        self.assertEqual(args.num_ports, "10")


# --- Run the Tests ---
if __name__ == "__main__":
    unittest.main()
