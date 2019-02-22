"""
    pyae.simple
    ===============
"""
import socket
import select
import logging

logging.basicConfig(level=logging.DEBUG)

def create_server(addr):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    sock.bind(addr)
    sock.listen(8046)

    sock.setblocking(False)

    return sock


def run(addr):
    socks = {}
    buffers = {}
    sock = create_server(addr)
    epoll = select.epoll(8046)

    epoll.register(sock.fileno(), select.EPOLLIN)

    while True:
        events = epoll.poll(0)
        for fd, event in events:
            if event & select.EPOLLIN:
                if fd == sock.fileno():
                    logging.info('fd.... {}'.format(fd))
                    conn, addr = sock.accept()
                    conn.setblocking(False)
                    epoll.register(conn.fileno(), select.EPOLLIN)
                    socks.setdefault(conn.fileno(), conn)
                    logging.info('{}: {} connected'.format(addr[0], addr[1]))
                else:
                    logging.info('ready fd.... {}'.format(fd))
                    ready_sock = socks[fd]
                    buffer = ready_sock.recv(8046)
                    buffers[fd] = buffer
                    logging.info(b'data received: ' + buffer)
                    epoll.modify(fd, select.EPOLLOUT | select.EPOLLIN)

            if event & select.EPOLLOUT:
                ready_sock = socks[fd]
                buffer = buffers[fd]
                ready_sock.sendall(buffer)
                logging.info(b'data sent: ' + buffer)
                epoll.modify(fd, select.EPOLLIN)

            if event & select.EPOLLHUP or event & select.EPOLLERR:
                logging.info('event {}'.format(event))
                epoll.unregister(fd)
                socks.pop(fd)
                buffers.pop(fd)

if __name__ == '__main__':
    run(('', 8080))
