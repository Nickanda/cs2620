# Coding Project Journal

## Table of Contents

- [February 5, 2025](#february-5-2025)
- [February 6, 2025](#february-6-2025)
- [February 7, 2025](#february-7-2025)
- [February 8, 2025](#february-8-2025)
- [February 10, 2025](#february-10-2025)
- [February 11, 2025](#february-11-2025)
- [Next Steps](#next-steps)

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
    - Messages are categorized by delivery status, optimizing frontend display logic.
  - Since usernames are unique, they function as reliable unique identifiers.

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

---

### February 8, 2025

#### Progress

- **Messaging System:**
  - Added UI and functionality for sending and deleting messages.

#### To-Do List

- Create backend functionality for all of the implemented frontend functions.

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

---

### February 11, 2025

#### Progress

- **Documentation:**
  - Added a README file to document the project setup, functionality, and usage.
- **Backend Enhancements:**
  - Implemented a JSON-based structure for the entire application.
  - Switched from Argon2 hashing to the deterministic Scrypt SHA-256 hashing algorithm.
- **Testing and Bug Fixes:**
  - Continued UI testing to identify and resolve any remaining bugs.
  - Fixed all tests to align with expected application behavior.

#### To-Do List

- Conduct a final review of tests to ensure correctness and stability.

---

### Next Steps

- Further refine the message object structure to optimize retrieval and update operations.
- Implement concurrency or multithreading to the frontend to allow for the UI to run separately of the socket
- Create real-time updates on the frontend
