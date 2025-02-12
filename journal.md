# Coding Project Journal

## Table of Contents

- [Coding Project Journal](#coding-project-journal)
  - [Table of Contents](#table-of-contents)
  - [Development Log](#development-log)
    - [February 5, 2025](#february-5-2025)
      - [Progress](#progress)
      - [Issues Encountered](#issues-encountered)
    - [February 6, 2025](#february-6-2025)
      - [Progress](#progress-1)
    - [February 7, 2025](#february-7-2025)
      - [Progress](#progress-2)
      - [To-Do List](#to-do-list)
    - [February 8, 2025](#february-8-2025)
      - [Progress](#progress-3)
      - [To-Do List](#to-do-list-1)
    - [February 10, 2025](#february-10-2025)
      - [Progress](#progress-4)
      - [To-Do List](#to-do-list-2)
    - [February 11, 2025](#february-11-2025)
      - [Progress](#progress-5)
      - [To-Do List](#to-do-list-3)
    - [Next Steps](#next-steps)
    - [JSON vs. Custom Wire Protocol](#json-vs-custom-wire-protocol)

## Development Log

### February 5, 2025

#### Progress

- Set up all necessary files for the frontend and backend.
- **Frontend:**
  - Chose Tkinter for the UI due to its simplicity and ease of use in Python.
  - Designed a basic UI for the signup form with additional logic for input validation.
  - Implemented Argon2 for password hashing before transmitting credentials to the server.
  - Established socket-based communication between the frontend and backend to handle actions (e.g., successful login, errors, etc.).
- **Backend:**
  - Used the multi-client, multi-operations example from class as a foundation.
  - Designed a wire protocol where the first word serves as a keyword to determine the action.
  - Defined action-dependent data transmission (e.g., login requires a username and password, while other actions may vary).
  - Set up the database system structure.

#### Issues Encountered

- The service connection function requires an early exit mechanism for filtering inputs. A helper function will resolve this.
- Incomplete data packets were received despite increasing buffer size. Further debugging is required.

[Back to Table of Contents](#table-of-contents)

---

### February 6, 2025

#### Progress

- **Resolved Issues:**
  - Implemented a helper function for filtering inputs within the service connection function.
  - Fixed data truncation by adjusting `data.outb` handling to ensure full packet transmission.
- **Backend Enhancements:**
  - Ensured the server runs independently of clients, preventing crashes upon client disconnection.
- **Database Structure Refinements:**

  - **Original Structure:**
    ```json
    [
      {
        "username": "string",
        "password": "string" // Argon2 hash
      },
      {
        "sender": "string", // must be a valid username
        "receiver": "string", // must be a valid username
        "message": "string",
        "delivered": "boolean"
      }
    ]
    ```
  - **Revised Structure:**

    - Usernames now serve as dictionary keys for O(1) lookup efficiency.
    - Since usernames are unique, they function as reliable unique identifiers.

    ```json
    {"username (string)":
      {"password": "string", // hashed
      "logged_in": "boolean",
      "addr": "int"},
      },
    ```

    - Messages are categorized by delivery status, optimizing frontend display logic.

    ```json
    {
      "undelivered": [
        {
          "sender": "string", // must be a valid username
          "receiver": "string", // must be a valid username
          "message": "string"
        }
      ],
      "delivered": [
        {
          "sender": "string", // must be a valid username
          "receiver": "string", // must be a valid username
          "message": "string"
        }
      ]
    }
    ```

[Back to Table of Contents](#table-of-contents)

---

### February 7, 2025

#### Progress

- **User Management:**
  - Enforced single-device login per user to prevent multiple simultaneous logins.
  - Implemented logout functionality to properly handle session termination.
- **Messaging System:**
  - Fixed issues with the messages database to ensure accurate message storage and retrieval.
  - The number of undelivered messages now refreshes automatically upon visiting the home page.
- **Frontend Enhancements:**
  - Created a home page with buttons for navigation to all other pages.
  - Added a user list page featuring a search bar, pagination, and user list display.

#### To-Do List

- Complete the home page functionality.
- Complete the messaging functionality.
- Implement backend for most functions.

[Back to Table of Contents](#table-of-contents)

---

### February 8, 2025

#### Progress

- **Messaging System:**
  - Added UI and functionality for sending and deleting messages.
  - Added a unique ID to each message to support the comma separated list design
    - New settings.json containing: `{"counter": "int"}`, to index message ids
    - Final messages.json structure:
    ```json
    {
      "undelivered": [
        {
          "id": "int", // unique for deletion
          "sender": "string", // must be a valid username
          "receiver": "string", // must be a valid username
          "message": "string"
        }
      ],
      "delivered": [
        {
          "id": "int", // unique for deletion
          "sender": "string", // must be a valid username
          "receiver": "string", // must be a valid username
          "message": "string"
        }
      ]
    }
    ```
    - Initially indexed by datetime but realized two users could send exactly the same message at the same time (for instance an empty message)

#### To-Do List

- Create backend functionality for all of the implemented frontend functions.

[Back to Table of Contents](#table-of-contents)

---

### February 10, 2025

#### Progress

- **Backend Enhancements:**
  - Added a global configuration file to maintain a counter for message IDs.
  - Created backend functionality for all existing frontend components.
  - Connected socket commands together to form a more cohesive application.
- **Bug Fixes:**
  - Resolved various miscellaneous code bugs encountered during implementation.
- **Testing:**
  - Started writing tests for the codebase.
  - Need to review and refine tests to ensure correct behavior.

#### To-Do List

- Review and refine tests to verify expected application behavior.

[Back to Table of Contents](#table-of-contents)

---

### February 11, 2025

#### Progress

- **Documentation:**
  - Added a README file to document the project setup, functionality, and usage.
  - Added many more comments to files for clarity, including a Last Updated field to inform future users of code.
- **Backend Enhancements:**
  - Implemented a JSON-based structure for the entire application.
  - Switched from Argon2 hashing to the deterministic Scrypt SHA-256 hashing algorithm.
  - This switch resolved segmentation faults we were running into.
- **Testing and Bug Fixes:**
  - Continued UI testing to identify and resolve any remaining bugs.
  - Fixed all tests to align with expected application behavior.

#### To-Do List

- Conduct a final review of tests to ensure correctness and stability.

[Back to Table of Contents](#table-of-contents)

---

### Next Steps

- Further refine the message object structure to optimize retrieval and update operations.
- Implement concurrency or multithreading to the frontend to allow for the UI to run separately of the socket
- Create real-time updates on the frontend

[Back to Table of Contents](#table-of-contents)

---

### JSON vs. Custom Wire Protocol (CWP)

We would expect that the JSON formatting of message transfer would have a higher transfer cost than the custom wire protocol. This is purely because our custom wire protocol can be designed so that we send only information that is absolutely essential. We would also be able to define exactly what each sequence of parameters is, allowing us to save additional space by not declaring what each parameter is.

We design an experiment below based on some of the most frequently used actions, as well as the sizes of the data transfer. To maintain consistency between JSON version and the CWP version, we utilize the following format: `COMMAND [...DATA]`, where `COMMAND` is a one-word (joined by underscores) command specifying the action, and the `...DATA` is optionally the data (either as a JSON object or as a list of parameters). This is to minimize the differences in displaying the command between the JSON version and the CWP version, while the data will be formatted in a custom way or the JSON way. We measure the difference in the size of the data.

| Command                | JSON Version (received data on server)                                                              | CWP Version (received data on server)                                |
| ---------------------- | --------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| login                  | `{"username": "3", "password": "4e07408562bedb8b60ce05c1decfe3ad16b72230967de01f640b7e4729b49fce"}` | `3 4e07408562bedb8b60ce05c1decfe3ad16b72230967de01f640b7e4729b49fce` |
| delete_message         | `{"delete_ids": "3", "current_user": "3"}`                                                          | `3 3`                                                                |
| get_delivered_messages | `{"username": "3", "num_messages": 34}`                                                             | `3 34`                                                               |
| get_user_list          | `{"search": "*"}`                                                                                   | `*`                                                                  |

| Command                | JSON Version (received data on client)                                                                         | CWP Version (received data on client) |
| ---------------------- | -------------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| login                  | `{"username": "3", "undeliv_messages": 0}`                                                                     | `3 0`                                 |
| delete_message         | `{"undeliv_messages": 0}`                                                                                      | `0`                                   |
| get_delivered_messages | `{"messages": [{"id": 10, "sender": "3", "message": "hello!"}, {"id": 11, "sender": "3", "message": "yes!"}]}` | `10_3_hello!11_3_yes!`                |
| get_user_list          | `{"user_list": ["a", "q", "123", "0", "2", "3", "4"]}`                                                         | `a q 123 0 2 3 4`                     |

We can immediately see that there is an increase in the size of the data that we sent to and from the server, just because there is a specified format for the data that we are transmitting. Despite the increase with the size in the data, we can also see that the data becomes a lot more interpretable to anyone reading the data in the JSON format when compared with the CWP format. For example, we can immediately see the message structure from the JSON format, including who the sender of the message is, what the ID of the message is, as well as the message itself, whereas it is not immediately obvious which chunk in the CWP format is the ID, the sender, or how messages are delineated (which is not shown here, but the null character separates each message).

For a small team, like the partner project that we used here, I believe that it would not be very hard for us to ensure that both of us know what the parameters on each end of the communication is. However, if we were to try this in a much larger company, perhaps with tens of people working on the same code, it would easily become confusing on what each part of the data in the CWP format corresponds to.

That being said, there are definitely speed benefits to the CWP format, since we are able to format it in the most efficient way possible, rather than having to rely on a pre-defined format. Thus, I would argue that if the team was looking to have the most efficient implementation without regard to the understanding of the data being transmitted, then the CWP format would be recommended. However, if there is a need for interpretability of the data, then I think that the JSON format would be better.

Of course, the ideal would be to control both the interpretability as well as the efficiency of the data on both the client and server (i.e., RPC) so that we are able to both understand the data but also work with it in the most efficient way possible.

[Back to Table of Contents](#table-of-contents)
