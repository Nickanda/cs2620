## Feb. 5, 2025

- Started setting up all of the files for the frontend and the backend
- On the frontend, I opted to use Tkinter as the UI choice because of its easy usability in Python and simple structure
  - Created some basic UI for the sign up form and added in some extra logic that checked for the
  - Implemented Argon2 for password hashing before transmitting the username and password to the server
  - Connected actions that would be sent from the backend to the frontend using the socket (e.g., successful login, errors, etc.)
- On the backend, I used the multi-client, multi-operations example that we had in class as the template
  - The format of the wire protocol that I constructed would use the first word as a keyword to determine the action
  - Every piece of data after that would be action-dependent (e.g., login would require a username and a password whereas other actions might need more/less)
  - Set up the database system that I would use

### Issues that came up:

- We need to exit the if statement within the service connection function in the server side in the middle (e.g., if we want to filter for inputs) - this can be done by a quick helper function
- For some reason, we are not receiving the entire packet of data given the size of the data - tried increasing buffer size but that doesn't seem to be changing anything

## Feb. 6, 2025

- Resolved the previous two issues - the first was implemented by the helper function, the second was resolved because we were only truncating the `data.outb` by the length of the sent message, which is not always guaranteed to be the same as the input message
- Added back in capability for the server to run independently of the clients - that is, if a client disconnects, the server won't also crash
- Our database structure originally had keys and values stored as follows:

```
[
  // User Object
  {
    "username": "string",
    "password": "string" // argon2 hash
  },

  // Message Object
  {
    "sender": "string", // must be in username
    "receiver": "string", // must be in username
    "message": "string",
    "delivered": "boolean",
    "timestamp": "string" // ISO 8601
  }
]
```

- As we started implementing the login and signup functionality in detail we realized that it instead would be helpful to have the usernames as the keys of our dictionary to take advantage of its properties and find whether a username had been previously registered in O(1).
- Furthermore, we realized that it would be useful to see messages by whether they were delivered or not because this determines the front-end display. As a result, we made a similar modification to make the message object be associated with delivered rather than our first-pass naive message object.
- We noted that in our case because we do not allow for repeats, the username can serve as a reasonable unique identifier. However, the messages are
