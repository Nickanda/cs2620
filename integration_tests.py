import os
import shutil
import threading
import time
import unittest
import grpc

import server  # Contains the serve() function
import chat_pb2
import chat_pb2_grpc
import database_wrapper


# -----------------------------------------------------------------------------
# Exhaustive Integration Test Suite
# -----------------------------------------------------------------------------
class ExhaustiveIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start the gRPC server in a background (daemon) thread.
        cls.server_thread = threading.Thread(
            target=lambda: server.serve(testing=True), daemon=True
        )
        cls.server_thread.start()
        # Give the server a moment to initialize.
        time.sleep(1)

        # Create a gRPC channel and stub using client settings.
        settings = database_wrapper.load_client_database()
        target = f"{settings['host']}:{settings['port']}"
        cls.channel = grpc.insecure_channel(target)
        cls.stub = chat_pb2_grpc.ChatServiceStub(cls.channel)

    @classmethod
    def tearDownClass(cls):
        # Close the channel; the daemonized server thread will exit when tests finish.
        cls.channel.close()

    # ---------------------------
    # Account Creation Tests
    # ---------------------------
    def test_create_account_valid(self):
        # Create a valid account.
        req = chat_pb2.CreateAccountRequest(username="UserA", password="passA")
        res = self.stub.CreateAccount(req)
        self.assertEqual(
            res.status, "success", msg="Valid account should be created successfully."
        )

        # Attempt to create a duplicate account.
        dup_res = self.stub.CreateAccount(req)
        self.assertEqual(
            dup_res.status, "error", msg="Duplicate account creation should fail."
        )
        self.assertIn("exists", dup_res.message)

    def test_create_account_invalid(self):
        # Attempt to create an account with a non-alphanumeric username.
        req_bad = chat_pb2.CreateAccountRequest(username="User@B", password="passB")
        bad_res = self.stub.CreateAccount(req_bad)
        self.assertEqual(
            bad_res.status,
            "error",
            msg="Username with non-alphanumeric characters should be rejected.",
        )

        # Attempt to create an account with an empty password.
        req_empty = chat_pb2.CreateAccountRequest(username="UserC", password="")
        empty_res = self.stub.CreateAccount(req_empty)
        self.assertEqual(
            empty_res.status, "error", msg="Empty password should be rejected."
        )

    # ---------------------------
    # Authentication (Login/Logout) Tests
    # ---------------------------
    def test_login_logout_flow(self):
        # Create a new account. (Accounts are created logged in by default.)
        req = chat_pb2.CreateAccountRequest(username="UserD", password="passD")
        self.stub.CreateAccount(req)
        # Logout so that we can test login.
        logout_res = self.stub.Logout(chat_pb2.LogoutRequest(username="UserD"))
        self.assertEqual(logout_res.status, "success")

        # Login with correct credentials.
        login_req = chat_pb2.LoginRequest(username="UserD", password="passD")
        login_res = self.stub.Login(login_req)
        self.assertEqual(
            login_res.status,
            "success",
            msg="Login with correct credentials should succeed.",
        )

        # Attempt to login again when already logged in.
        login_again = self.stub.Login(login_req)
        self.assertEqual(
            login_again.status,
            "error",
            msg="Re-login when already logged in should fail.",
        )
        self.assertIn("already logged in", login_again.message)

        # Logout and then attempt to login with an incorrect password.
        self.stub.Logout(chat_pb2.LogoutRequest(username="UserD"))
        wrong_login = self.stub.Login(
            chat_pb2.LoginRequest(username="UserD", password="wrong")
        )
        self.assertEqual(
            wrong_login.status,
            "error",
            msg="Login with an incorrect password should fail.",
        )
        self.assertIn("Incorrect", wrong_login.message)

    # ---------------------------
    # Messaging Tests
    # ---------------------------
    def test_send_message_offline_online(self):
        # Create a sender and a receiver.
        self.stub.CreateAccount(
            chat_pb2.CreateAccountRequest(username="Sender1", password="pass")
        )
        self.stub.CreateAccount(
            chat_pb2.CreateAccountRequest(username="Receiver1", password="pass")
        )
        # Ensure Receiver1 is offline.
        self.stub.Logout(chat_pb2.LogoutRequest(username="Receiver1"))
        # Login the sender.
        self.stub.Login(chat_pb2.LoginRequest(username="Sender1", password="pass"))

        # Send a message to an offline receiver (should go to undelivered).
        send_res = self.stub.SendMessage(
            chat_pb2.SendMessageRequest(
                sender="Sender1", receiver="Receiver1", message="Hello offline"
            )
        )
        self.assertEqual(send_res.status, "success")

        # Now login the receiver.
        login_receiver = self.stub.Login(
            chat_pb2.LoginRequest(username="Receiver1", password="pass")
        )
        self.assertEqual(login_receiver.status, "success")

        # Send another message while Receiver1 is online (should be delivered immediately).
        send_res2 = self.stub.SendMessage(
            chat_pb2.SendMessageRequest(
                sender="Sender1", receiver="Receiver1", message="Hello online"
            )
        )
        self.assertEqual(send_res2.status, "success")

        # Retrieve undelivered messages; should include the offline message.
        undelivered = self.stub.GetUndelivered(
            chat_pb2.GetUndeliveredRequest(username="Receiver1", num_messages=10)
        )
        self.assertEqual(undelivered.status, "success")
        self.assertGreaterEqual(
            len(undelivered.messages),
            1,
            msg="At least one undelivered message expected.",
        )

        # Retrieve delivered messages; should include the online message.
        delivered = self.stub.GetDelivered(
            chat_pb2.GetDeliveredRequest(username="Receiver1", num_messages=10)
        )
        self.assertEqual(delivered.status, "success")
        self.assertGreaterEqual(
            len(delivered.messages), 1, msg="At least one delivered message expected."
        )

    def test_delete_message(self):
        # Create sender and receiver.
        self.stub.CreateAccount(
            chat_pb2.CreateAccountRequest(username="Sender2", password="pass")
        )
        self.stub.CreateAccount(
            chat_pb2.CreateAccountRequest(username="Receiver2", password="pass")
        )
        # Ensure Receiver2 is offline.
        self.stub.Logout(chat_pb2.LogoutRequest(username="Receiver2"))
        # Login Sender2.
        self.stub.Login(chat_pb2.LoginRequest(username="Sender2", password="pass"))

        # Send several messages.
        for i in range(3):
            send_req = chat_pb2.SendMessageRequest(
                sender="Sender2", receiver="Receiver2", message=f"Msg {i}"
            )
            send_res = self.stub.SendMessage(send_req)
            self.assertEqual(send_res.status, "success")

        # Login Receiver2 so that messages can be retrieved.
        self.stub.Login(chat_pb2.LoginRequest(username="Receiver2", password="pass"))
        undelivered = self.stub.GetUndelivered(
            chat_pb2.GetUndeliveredRequest(username="Receiver2", num_messages=10)
        )
        self.assertEqual(undelivered.status, "success")
        msg_ids = [msg.id for msg in undelivered.messages]
        self.assertTrue(
            len(msg_ids) >= 1, msg="At least one message should have been retrieved."
        )

        # Delete the first retrieved message.
        del_req = chat_pb2.DeleteMessageRequest(
            username="Receiver2", message_ids=[msg_ids[0]]
        )
        del_res = self.stub.DeleteMessage(del_req)
        self.assertEqual(del_res.status, "success")

        # Verify that the deleted message is no longer in delivered messages.
        delivered = self.stub.GetDelivered(
            chat_pb2.GetDeliveredRequest(username="Receiver2", num_messages=10)
        )
        for msg in delivered.messages:
            self.assertNotEqual(
                msg.id,
                msg_ids[0],
                msg="Deleted message should not appear in delivered messages.",
            )

    # ---------------------------
    # Account Deletion Test
    # ---------------------------
    def test_delete_account(self):
        # Create two users. UserE will be deleted.
        self.stub.CreateAccount(
            chat_pb2.CreateAccountRequest(username="UserE", password="pass")
        )
        self.stub.CreateAccount(
            chat_pb2.CreateAccountRequest(username="UserF", password="pass")
        )
        # Send a message from UserF to UserE.
        send_req = chat_pb2.SendMessageRequest(
            sender="UserF", receiver="UserE", message="Hello"
        )
        self.stub.SendMessage(send_req)

        # Delete UserE.
        del_req = chat_pb2.DeleteAccountRequest(username="UserE")
        del_res = self.stub.DeleteAccount(del_req)
        self.assertEqual(del_res.status, "success")

        # Verify that UserE can no longer log in.
        login_res = self.stub.Login(
            chat_pb2.LoginRequest(username="UserE", password="pass")
        )
        self.assertEqual(
            login_res.status,
            "error",
            msg="Deleted account should not be able to log in.",
        )

        # Also, verify that messages involving UserE have been purged.
        delivered = self.stub.GetDelivered(
            chat_pb2.GetDeliveredRequest(username="UserF", num_messages=10)
        )
        for msg in delivered.messages:
            self.assertNotIn(
                "UserE",
                [msg.sender, "UserE"],
                msg="Messages involving deleted account should be removed.",
            )

    # ---------------------------
    # User Search Tests
    # ---------------------------
    def test_search_users(self):
        # Create a set of users for search testing.
        users_to_create = ["Alice", "Alicia", "Bob", "Charlie", "Alex"]
        for uname in users_to_create:
            req = chat_pb2.CreateAccountRequest(username=uname, password="pass")
            self.stub.CreateAccount(req)
            # Logout so they are available for search.
            self.stub.Logout(chat_pb2.LogoutRequest(username=uname))

        # Search using pattern "Ali*" (should return "Alice" and "Alicia").
        search_req = chat_pb2.SearchUsersRequest(pattern="Ali*")
        search_res = self.stub.SearchUsers(search_req)
        self.assertEqual(search_res.status, "success")
        self.assertIn("Alice", search_res.users)
        self.assertIn("Alicia", search_res.users)

        # Search using "*" (should return all users).
        search_all_req = chat_pb2.SearchUsersRequest(pattern="*")
        search_all_res = self.stub.SearchUsers(search_all_req)
        self.assertEqual(search_all_res.status, "success")
        self.assertGreaterEqual(
            len(search_all_res.users),
            len(users_to_create),
            msg="Wildcard search should return all created users.",
        )

    # ---------------------------
    # Refresh Home Tests
    # ---------------------------
    def test_refresh_home(self):
        # Create a user for the refresh home test.
        self.stub.CreateAccount(
            chat_pb2.CreateAccountRequest(username="UserG", password="pass")
        )
        # Ensure UserG is offline.
        self.stub.Logout(chat_pb2.LogoutRequest(username="UserG"))

        # Create a sender and send a message to UserG.
        self.stub.CreateAccount(
            chat_pb2.CreateAccountRequest(username="Sender3", password="pass")
        )
        send_req = chat_pb2.SendMessageRequest(
            sender="Sender3", receiver="UserG", message="Refresh home message"
        )
        self.stub.SendMessage(send_req)

        # Call RefreshHome RPC.
        refresh_req = chat_pb2.RefreshHomeRequest(username="UserG")
        refresh_res = self.stub.RefreshHome(refresh_req)
        self.assertEqual(refresh_res.status, "success")
        self.assertGreaterEqual(
            refresh_res.undeliv_messages,
            1,
            msg="RefreshHome should indicate undelivered messages.",
        )

    # ---------------------------
    # Edge Case Tests
    # ---------------------------
    def test_edge_cases(self):
        # Test sending a message with an empty message body.
        self.stub.CreateAccount(
            chat_pb2.CreateAccountRequest(username="EdgeUser1", password="pass")
        )
        self.stub.CreateAccount(
            chat_pb2.CreateAccountRequest(username="EdgeUser2", password="pass")
        )
        # Ensure receiver is offline.
        self.stub.Logout(chat_pb2.LogoutRequest(username="EdgeUser2"))
        # Login sender.
        self.stub.Login(chat_pb2.LoginRequest(username="EdgeUser1", password="pass"))
        # Send a message with an empty message body.
        send_empty = self.stub.SendMessage(
            chat_pb2.SendMessageRequest(
                sender="EdgeUser1", receiver="EdgeUser2", message=""
            )
        )
        self.assertEqual(
            send_empty.status,
            "success",
            msg="Sending an empty message should succeed if not explicitly disallowed.",
        )

        # Test GetUndelivered with num_messages = 0.
        undeliv_zero = self.stub.GetUndelivered(
            chat_pb2.GetUndeliveredRequest(username="EdgeUser2", num_messages=0)
        )
        self.assertEqual(
            undeliv_zero.status,
            "error",
            msg="Requesting 0 messages should result in an error or empty response.",
        )

        # Test searching with an empty pattern.
        search_empty = self.stub.SearchUsers(chat_pb2.SearchUsersRequest(pattern=""))
        self.assertEqual(
            search_empty.status,
            "success",
            msg="Empty search pattern should default to '*' behavior.",
        )
        self.assertTrue(len(search_empty.users) > 0)


if __name__ == "__main__":
    unittest.main()
