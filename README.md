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

Open up at least two terminal windows. In one terminal window, run the following command: `python main.py`. In the other terminal window, run the following command: `python client.py`. This will launch the server (`main.py`) and also the client (`client.py`). A graphical interface will show up - click on that and follow the UI to either sign up or login!

To create more than one connecting client, run `python client.py` in a separate terminal window - each new terminal window will create a new client.

**Note:** Each account can only be logged in at one location at a time - this is to prevent any quirks from occurring when more than one device logs into the device at a time (e.g., deleting an account from one window while another window is still logged in).

## Running with JSON Variants

To run the server and client with the JSON variants, you will have to append `_json` to the end of the run file. In other words, to run the server, you will have to run `python main_json.py`, and to run the client, you will need to run `python client_json.py`.

**Please note**: Because the two variants use inherently different communication protocols, we enforce no cross-communication by default by having the server on different ports (54400 for the default variant, 54444 for the JSON variant). It _is_ possible to run both servers at the same time, but will cause instability within the server and database and is _never_ recommended.

## Credits

This project is created by Nicholas Yang and Victoria Li. Portions of the code is created from generative AI, but may be modified. An exhaustive list of where this code can be found is listed here:

- Within our unit and integration tests
- For the styling and layout of the UI
