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

### To run the client and server locally:

Open up at least two terminal windows. In one terminal window, run the following command: `python main.py`. In the other terminal window, run the following command: `python client.py`. This will launch the server (`main.py`) and also the client (`client.py`).

## Running with JSON Variants

To run the server and client with the JSON variants, you will have to append `_json` to the end of the run file. In other words, to run the server, you will have to run `python main_json.py`, and to run the client, you will need to run `python client_json.py`.

**Please note**: Because the two variants use inherently different communication protocols, we enforce no cross-communication by default by having the server on different ports (54400 for the default variant, 54444 for the JSON variant). It _is_ possible to run both servers at the same time, but will cause instability within the server and database and is _never_ recommended.
