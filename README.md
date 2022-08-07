# gpcp - General Purpose Connection Protocol
A simple framework written in Python 3 created to make it easier to create socket servers and clients.

## Installation
Install gpcp using the `setup.py` file: just run `python3 -m pip install .` in the root folder. Then you can `import gpcp` from anywhere.

gpcp is not ready yet, but if you want to try it you are free to use it.

## Examples
Some simple examples are available in the [examples/](examples/) folder.

## Contributing
The roadmap is available on [Trello](https://trello.com/b/wzVH18Fd/gpcp "GPCP On Trello"). Now gpcp is not so ready to use it in projects but it will, if you find problems or want to give a suggestion please open an issue here.

## Testing

Testing the project requires the following `pip` packages: `pytest`, `pytest-reraise`.

Just run `pytest` in the root directory to run all tests.

## Logging

To save gpcp logs to file in your application, use the following code:

```python
import logging
logging.basicConfig(filename="./logs.txt", level=logging.DEBUG, force=True)
```