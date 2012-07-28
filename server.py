import sys
import socket
import threading
import select

import worker
from manager import Manager
from logger import Logger
from expiration import Expiration

class Server:

    def __init__(self, options):
        self.options = options
        self.running = True
        self.connections = {}
        self.manager = Manager(self, self.options)
        self.manager.start()
        self.expiration = Expiration(self.options.cleanup_interval, self.options.ttl)
        self.expiration.start()

    def stop(self):
        self.running = False

    def run(self):

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.options.host, self.options.port))
        sock.listen(self.options.backlog)
        sock.setblocking(0)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        listener = sock.fileno()
        epoll = select.epoll()
        epoll.register(listener, select.EPOLLIN | select.EPOLLOUT | select.EPOLLHUP)

        Logger.info("ItemReservation server started")

        try:
            while self.running:
                events = epoll.poll()
                for fd, event in events:

                    if fd == listener:
                        # New connection
                        (clientsock, address) = sock.accept()
                        clientsock.setblocking(0)
                        fileno = clientsock.fileno()
                        epoll.register(fileno, select.EPOLLIN)
                        self.connections[fileno] = {
                            'sock': clientsock, 
                            'addr': address
                        }
                    elif event & select.EPOLLIN:
                        # incoming data from client
                        if self.manager.dispatch(self.connections[fd]) != True:
                            # Client closed connection
                            self.connections[fileno]['sock'].shutdown(socket.SHUT_RDWR)
                            epoll.modify(fileno, 0)
                    elif event & select.EPOLLHUP:
                        # socket shutdown
                        epoll.unregister(fd)
                        addr = self.connections[fd]['addr']
                        Logger.info(addr[0] + ":" + str(addr[1]) + " left")
                        self.connections[fd]['sock'].close()
                        del self.connections[fd]

        except:
            Logger.exception(__file__ + ":" + str(sys.exc_info()))
            self.stop()

        Logger.debug("shutting down")
        epoll.unregister(listener)
        epoll.close()
        sock.close()
      
        Logger.debug("stopping manager") 
        self.manager.stop()
        self.manager.join()
        Logger.debug("waiting for the cleanup thread to finish")
        self.expiration.stop()
        self.expiration.join()

        Logger.info("ItemReservation server ended")
