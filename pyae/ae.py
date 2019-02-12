"""
    pyae.ae
    ===========
    A asynchronous event loop written with Python, inspired by redis
    event-driven programming library. The link is https://github.com/antirez/redis/blob/unstable/src/ae.c
"""
import select


AE_NONE = 0
AE_READABLE = 1
AE_WRITEABLE = 2
AE_BARRIER = 4


class FileEvent:

    def __init__(self, mask=AE_NONE, client=None):
        self.mask = mask
        self.client = client
        self.rproc = None
        self.wproc = None
        self.r_buffers = bytearray()
        self.w_buffers = bytearray()


class EventLoop:

    def __init__(self, size=4096):
        self.fes = [FileEvent() for _ in range(size)]
        self.stop = 1
        self.maxfd = 0
        self.epoll = select.epoll(size)

    def create_fe(self, fd, mask, proc, client):
        # todo: if fd is greater than the event loop size, raise a exception
        fe = self.fes[fd]
        epoll_mask = 0

        if mask & AE_READABLE:
            fe.rproc = proc
            epoll_mask |= select.EPOLLIN
        if mask & AE_WRITEABLE:
            fe.wproc = proc
            epoll_mask |= select.EPOLLOUT

        if client:
            fe.client = client

        if fe.mask == AE_NONE:
            fe.mask |= mask
            self.epoll.register(fd, epoll_mask)
        else:
            fe.mask |= mask
            self.epoll.modify(fd, epoll_mask)

        if fd > self.maxfd:
            self.maxfd = fd

    def delete_fe(self, fd, delmask):
        if fd > self.maxfd:
            return

        fe = self.fes[fd]

        if fe.mask == AE_NONE:
            return

        mask = fe.mask & (~delmask)
        epoll_mask = 0

        if mask & AE_READABLE:
            epoll_mask |= select.EPOLLIN
        if mask & AE_WRITEABLE:
            epoll_mask |= select.EPOLLOUT

        if mask != AE_NONE:
            self.epoll.modify(fd, epoll_mask)
        else:
            self.epoll.unregister(fd)

        # update maxfd can improve performance
        if fd == self.maxfd and fe.mask == AE_NONE:
            tmp = self.maxfd - 1
            while tmp >= 0:
                if self.fes[tmp].mask != AE_NONE:
                    break
                tmp -= 1
            self.maxfd = tmp

    def process_fes(self):
        processed = 0
        if self.maxfd != -1:
            events_list = self.epoll.poll(0)

            if events_list and len(events_list):
                for fd, events in events_list:
                    mask = 0
                    fe = self.fes[fd]
                    if events & select.EPOLLIN:
                        mask |= AE_READABLE
                    if events & select.EPOLLOUT:
                        mask |= AE_WRITEABLE
                    if events & select.EPOLLERR:
                        mask |= AE_WRITEABLE
                    if events & select.EPOLLHUP:
                        mask |= AE_WRITEABLE

                    if events & select.EPOLLIN:
                        fe.rproc(self, fd, mask)

                    if events & select.EPOLLOUT:
                        fe.wproc(self, fd, mask)

                    processed += 1
        return processed

    def run(self):
        self.stop = 0
        while not self.stop:
            self.process_fes()
