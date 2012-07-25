import socket
import threading
import worker
import manager
import select

class Server:
    def __init__(self, options):
        self.options = options
        self.manager = manager.Manager(self.options)
        self.manager.start()

    def run(self):

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.options.host, self.options.port))
        sock.listen(self.options.backlog)
        sock.setblocking(0)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        listener = sock.fileno()
        epoll = select.epoll()
        epoll.register(listener, select.EPOLLIN)
        connections = {}

        try:
            while True:
                events = epoll.poll()
                for fd, event in events:

                    if fd == listener:
                        ""
                        (clientsock, address) = sock.accept()
                        clientsock.setblocking(0)
                        fileno = clientsock.fileno()
                        epoll.register(fileno, select.EPOLLIN)
                        connections[fileno] = {'sock': clientsock, 'addr': address}
                    elif event & select.EPOLLIN:
                        self.manager.dispatch(connections[fd])
                    elif event & select.EPOLLHUP:
                        epoll.unregister(fd)
                        connections[fd]['sock'].close()
                        del connections[fd]

        finally:
            epoll.unregister(listener)
            epoll.close()
            sock.close()
        
        self.manager.notifyJoin() 
        self.manager.join()
