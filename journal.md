# Coding Project Journal

## Link to Project

https://github.com/Nickanda/cs2620

## Table of Contents

- [Coding Project Journal](#coding-project-journal)
  - [Table of Contents](#table-of-contents)
  - [Development Log](#development-log)
    - [February 5, 2025](#february-5-2025)
      - [Progress](#progress)
      - [Issues Encountered](#issues-encountered)

## Development Log

### March 21, 2025

#### Progress

- Started remaking the backend infrastructure to being class-based
- Shifted the versioning and command data into part of the JSON data that we transmit
- Adjusted all of the necessary frontend components to be compatible with the new JSON format
- Started writing an internal communicator class, which would handle the communication between replicas of the server
- Ported over the database wrapper so that multiple servers could port with a unique database

#### Issues Encountered

- No issues encountered, but did not test porting over the new JSON formatting, will note to test that

[Back to Table of Contents](#table-of-contents)

---

### March 22, 2025

#### Progress

- Rewrote the entire server to be class-based so that we can create multiple instances of the server using processes on the backend
- Integrated the internal communicator class with the new server class
- Created new methods for each of the different command types that the frontend would send to the backend

- Currently, the setup for the 3-fault system is that the client and the server will have a list of total possible combinations of hosts and ports - we define this using a list of comma-separated ports, the starting port number, and the maximum number of ports allowed on each machine
- This should allow us to freely adjust how many replicas we can start with, while allowing freedom down the line if we want to spontaneously spin up more replicas and add them to our system
- On the client side, they will go in order to test each of the available sockets until they reach one of the sockets that will work - this inherently means that the client will know every possible replica that can be made, but is a necessary component unless we rebind the ports on which the sockets are bound to (which is a possible solution that we can look into)
  - The main concern with this is that the release of a port by one of the servers will take approximately ten seconds before it can be reallocated, and we would have to be able to consistently reassign ports somehow if we were to do this
- We've implemented the process of checking whether the other ports are alive on the server side and sending updates, but need to make sure that the updates that we send won't also send a client update (it should only internally update the database and nothing else)
- The original intent of the internal communication was to send the client-side update to the other servers, but I'm wondering if it's worth looking into creating an editing format for internal communications (e.g., add this data to the messages file), or whether we should just communicate the entire new database
- Also need to note that we need to communicate the latest database once a replica joins the network so that we can sync all of the replicas together

#### Issues Encountered

- No issues encountered, but did not test porting over the new JSON formatting, will note to test that

[Back to Table of Contents](#table-of-contents)

---

### March 23, 2025

#### Progress

- Finished the rest of the implementation and finally started booting up our system on my local computer
- Ran into some interesting issues in our implementation:
  - First, we see that the internal communication network is a little buggy because some of our updates are extremely long (since we are communicating the whole database on initial startup) - this is solved by increasing how many bytes of data we can receive at a time.
  - When multiple machines were connected at a time, we noticed that there were oftentimes multiple data pieces in `data.outb`, so we utilize the null character `\0` as a separator between each of the data pieces
- Integrated the client side with the servers that we have available and confirmed that it will test
 
#### Issues Encountered

- No issues encountered, but did not test porting over the new JSON formatting, will note to test that

[Back to Table of Contents](#table-of-contents)
