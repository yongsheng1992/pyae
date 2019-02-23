# pyae

pyae(python asynchronous event loop)，是一个模仿redis的异步事件编程库的python版本。只用来处理TCP网络编程。

实现的EchoServer代码很凌乱，但是会不断的改进。

首先写一个面向过程的echo服务程序，然后在根据实际遇到的问题，修改成面向对象的版本。

## 简单的epoll使用

在[epoll(7)](http://man7.org/linux/man-pages/man7/epoll.7.html)中给了epoll的使用例子。我们的编程就从这里开始。

```c
#define MAX_EVENTS 10
struct epoll_event ev, events[MAX_EVENTS];
int listen_sock, conn_sock, nfds, epollfd;

/* Code to set up listening socket, 'listen_sock',
  (socket(), bind(), listen()) omitted */

epollfd = epoll_create1(0);
if (epollfd == -1) {
   perror("epoll_create1");
   exit(EXIT_FAILURE);
}

ev.events = EPOLLIN;
ev.data.fd = listen_sock;
if (epoll_ctl(epollfd, EPOLL_CTL_ADD, listen_sock, &ev) == -1) {
   perror("epoll_ctl: listen_sock");
   exit(EXIT_FAILURE);
}

for (;;) {
   nfds = epoll_wait(epollfd, events, MAX_EVENTS, -1);
   if (nfds == -1) {
       perror("epoll_wait");
       exit(EXIT_FAILURE);
   }

   for (n = 0; n < nfds; ++n) {
       if (events[n].data.fd == listen_sock) {
           conn_sock = accept(listen_sock,
                              (struct sockaddr *) &addr, &addrlen);
           if (conn_sock == -1) {
               perror("accept");
               exit(EXIT_FAILURE);
           }
           setnonblocking(conn_sock);
           ev.events = EPOLLIN | EPOLLET;
           ev.data.fd = conn_sock;
           if (epoll_ctl(epollfd, EPOLL_CTL_ADD, conn_sock,
                       &ev) == -1) {
               perror("epoll_ctl: conn_sock");
               exit(EXIT_FAILURE);
           }
       } else {
           do_use_fd(events[n].data.fd);
       }
   }
}
```
可以总结一下：
* epoll只关心文件描述符和事件类型
* 一个事件一般和(fd, mask, handlers)相关

这样可以封装一个`FileEvent`类出来：
```python

AE_READABLE = 1
AE_WRITEABLE = 2
AE_BARRIER = 4


class FileEvent:
    
    def __init__(self, fd, mask, proc):
        self.fd = fd
        self.rproc = None
        self.wproc = None
        if mask | AE_READABLE:
            self.rproc = proc
        if mask | AE_WRITEABLE:
            self.wproc = proc 
```

但是毕竟Python封装了较高级的API，不像c一样，即使对于socket连接，也可以直接对socket的文件描述符直接进行读和写操作。最好使用标准库`socket`封装好的读和写的API。所以需要对前面的`FileEvent`类进行改造：
```python

class FileEvent:
    
    def __init__(self, fd, mask, proc, client=None):
        self.client = client

```

在构造方法的参数加上了一个client。如果这样做初始化：
```python
conn, addr = sock.accept()
fe = FileEvent(conn.fileno(), AE_READABLE, proc, conn)
```

那么当fd可读的时候，可以调用`fe.client.read`方法。

