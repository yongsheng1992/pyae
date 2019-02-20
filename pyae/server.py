"""
    pyae.server
    ===========
    A simple TCP server implemented by pyae event loop.
"""
import socket
from .ae import EventLoop, AE_READABLE


class Server:

    def __init__(self, address):
        self.address = address
        self.el = EventLoop()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR)

    def handle_read(self, ae: EventLoop, fd, mask):
        pass

    def handle_write(self, ae: EventLoop, fd, mask):
        pass

    def handle_accept(self, ae: EventLoop, fd, mask):
        conn, addr = self.sock.accept()
        self.el.create_fe(conn.fileno(), fd, AE_READABLE)

    def run(self):
        self.sock.bind(self.address)
        self.sock.listen(8046)
        self.sock.setblocking(False)
        self.el.create_fe(self.sock.fileno(), AE_READABLE, self.handle_accept)
