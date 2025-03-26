# Coding Project Journal

## Link to Project

https://github.com/Nickanda/cs2620

## Table of Contents

- [Coding Project Journal](#coding-project-journal)
  - [Link to Project](#link-to-project)
  - [Table of Contents](#table-of-contents)
  - [Development Log](#development-log)
    - [Design of the System](#design-of-the-system)
    - [March 21, 2025](#march-21-2025)
      - [Progress](#progress)
      - [Issues Encountered](#issues-encountered)
    - [March 22, 2025](#march-22-2025)
      - [Progress](#progress-1)
      - [Issues Encountered](#issues-encountered-1)
    - [March 23, 2025](#march-23-2025)
      - [Progress](#progress-2)
      - [Issues Encountered](#issues-encountered-2)
    - [March 23, 2025](#march-23-2025-1)
      - [Progress](#progress-3)
      - [Issues Encountered](#issues-encountered-3)

## Development Log

### Design of the System

The design of our system lies upon the servers having an internally communicating network and the clients polling every possible server to see if there is a connection that can be made (and to also check if the server is still alive) - we do this by using threads within each process to host the internal network. Within each server, we elect a new leader by taking the minimum value of the host and port values combined as a string to ensure uniqueness and subsequently take that leader as the golden source of truth (that leader will propagate its database to all of the other servers).

Each server maintains its own internal connection pool of other servers, and pings each other to ensure that everyone is alive. When a server goes down within this connection pool, they will be removed from the connection pool and will be subsequently polled to see if it comes back up. A new leader election will occur if the server that went down was the leader. This also means that we can start up servers that went down or start up new servers and the other servers will detect that (given that it is within the detection range) and add it to the connection pool.

On the client side, an array of possible connectable servers is made and is tested every time to check the list of available servers in addition to making sure that if any servers go down, we remove them from the array of connectable servers. When we make a request, we take the first connectable server that we can use and send requests to that.

On the server internal network, we also have servers propagate changes that they receive if it's from the client - this will send the update to other servers within the internal network so that the other servers can propagate these changes onto their databases. This will allow all of the servers to remain on the same page whenever a client makes an update or change.

Through this system, we can fire up three servers on any two computers, start up any number of clients, and send down two of the three servers and have the client still function. We can also then start up new servers, have those new servers receive the latest database from the leader and become new replicas of the leader.

[Back to Table of Contents](#table-of-contents)

---

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
- Implementation worked on just my computer with multiple servers running on my computer!
- Added in tests for our implementation of the messaging app

---

### March 24, 2025

#### Progress

- We tested whether the system would work on more than one computer and ended up having some issues with connecting the client to servers that were not located on the computer
- We ended up redoing the entire server polling mechanism so that it would check every server at the same time rather than only getting one at a time
- Ran tests and confirmed that our application works with multiple clients across multiple servers and multiple clients, and that adding new servers on the go would work (given that the new server is on one of the predefined ports)

[Back to Table of Contents](#table-of-contents)
