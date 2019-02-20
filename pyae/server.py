"""
    pyae.server
    ===========
    A simple TCP server implemented by pyae event loop.
"""
import socket
import errno
from .ae import EventLoop, AE_READABLE, AE_WRITEABLE


class Server:

    def __init__(self, address):
        self.address = address
        self.el = EventLoop()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR)

    def handle_read(self, el: EventLoop, fd, mask):
        fe = el.fes[fd]
        client = fe.client
        r_buffers = fe.r_buffers

        while True:
            try:
                buffers = client.recv(4096)
                r_buffers += buffers
            except socket.error as e:
                err = e.args[0]
                if err in (errno.EAGAIN, errno.EWOULDBLOCK):
                    break

        before, seq, after = r_buffers.partition(b'\n')

        if seq:
            fe.w_buffers = before + seq
            el.create_fe(fd, AE_WRITEABLE, self.handle_write, None)
            fe.r_buffers = after

    def handle_write(self, el: EventLoop, fd, mask):
        fe = el.fes[fd]
        client = fe.client
        w_buffers = fe.w_buffers
        client.sendall(w_buffers)
        # todo: optimize it
        el.delete_fe(fd, mask)

    def handle_accept(self, el: EventLoop, fd, mask):
        fe = el.fes[fd]
        fe.mask = mask
        client = fe.client

        conn, addr = client.accept()
        conn.setblocking(False)
        el.create_fe(conn.fileno(), AE_READABLE, self.handle_read, conn)

    def run(self):
        self.sock.bind(self.address)
        self.sock.listen(8046)
        self.sock.setblocking(False)
        self.el.create_fe(self.sock.fileno(), AE_READABLE, self.handle_accept, self.sock)
        self.el.run()
