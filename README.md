# CS2620 Design Exercise 1

## Installation

Our project uses only libraries that are included in the default Python installation. Importantly, we rely on the following:

- `hashlib` for password hashing
- `tkinter` for UI interface
- `socket` and `selectors` for socket handling
- `unittest` for our unit and integration tests

This was run on the Python 3.11.0, but should be compatible with Python versions 3.10.0 and above. Some MacOS users may still use an outdated version of `tkinter`, depending on whether the user is using the natively-supported `tkinter` or the `tkinter` that comes with the Python installation. Verify the versions by running these in your command line:

```zsh
$ python --version
Python 3.11.0 # This should be >= 3.10.0

$ python
>>> import tkinter
>>> tkinter.TkVersion
8.6
```

If the versions you see here do not line up, please follow the official steps to upgrade your versions.

## Running the Application

### Running the Server

There are a number of options that should be specified for the program to work. First, you will need to get your network IP - this can be found with the command `ipconfig getifaddr en0`. If you are running this on multiple computers, you should also run this command on the other computer as you will need this.

We list out each of the possible parameters below and their corresponding definitions as well as an example:

| Parameter                  | Definition                                                                                                                                  | Example                                   |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| `--host`                   | The IP address of the server to bind to.                                                                                                    | `--host 10.250.208.250`                   |
| `--start_server_port`      | The port number on which the server will listen.                                                                                            | `--start_server_port 50000`               |
| `--num_servers`            | The number of servers that will be launched                                                                                                 | `--num_servers 1`                         |
| `--start_internal_port`    | The port number on which the internal server will listen.                                                                                   | `--start_internal_port 60000`             |
| `--internal_other_servers` | Comma-separated list of other hosts that the internal server can connect to.                                                                | `--internal_other_servers 10.250.208.250` |
| `--internal_other_ports`   | Comma-separated list of other ports that the internal server can connect to, matching the host from the `internal_other_servers`.           | `--internal_other_ports 60000`            |
| `--internal_max_ports`     | Comma-separated list of maximum number of ports that the internal server should sweep, matching the host from the `internal_other_servers`. | `--internal_max_ports 10`                 |

The command that I used to start up my server is:

```
python3 main_distributed.py --internal_other_servers 10.250.208.250,10.250.99.41 --internal_other_ports 60000,60000 --internal_max_ports 10,10 --num_servers 1 --start_internal_port 60005 --start_server_port 50005 --host 10.250.208.250
```

The command that Victoria started up on the other computer was:

```
python3 main_distributed.py --internal_other_servers 10.250.208.250,10.250.99.41 --internal_other_ports 60000,60000 --internal_max_ports 10,10 --num_servers 1 --start_internal_port 60000 --start_server_port 50000 --host 10.250.99.41
```

I ran multiple servers on my own computer by adjusting the `start_internal_port` and `start_server_port` parameters to different numbers (usually corresponding with each other, but not required).

### Running the Client

Similar to the server, there are multiple options on running the client-side code to make sure that the client can connect to every possible server. We do this with the following parameters:

| Parameter     | Definition                                                                                          | Example                  |
| ------------- | --------------------------------------------------------------------------------------------------- | ------------------------ |
| `--hosts`     | Comma-separated list of hosts that the client can connect to.                                       | `--hosts 10.250.208.250` |
| `--ports`     | Comma-separated list of ports that the client can connect to, corresponding to each of the hosts.   | `--ports 50000`          |
| `--num_ports` | Comma-separated list of the number of ports to sweep across for each of the defined hosts and ports | `--num_ports 10`         |

The command that I used to start up a client (on either computer) is:

```
python3 client_json.py --hosts 10.250.208.250,10.250.99.41 --ports 50000,50000 --num_ports 10,10
```

## Credits

This project is created by Nicholas Yang and Victoria Li. Portions of the code is created from generative AI, but may be modified. An exhaustive list of where this code can be found is listed here:

- Within our unit and integration tests
- For the styling and layout of the UI
