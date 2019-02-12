"""
    pyae.server
    ===========
    A simple TCP server implemented by pyae event loop.
"""
from .ae import EventLoop


class Server:

    def __init__(self, address):
        self.address = address
        self.el = EventLoop()
