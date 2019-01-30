"""
    pyae.server
    ===========
    A simple TCP server implemented by pyae event loop.
"""

class Server:

    def __init__(self, address):
        self.address = address
