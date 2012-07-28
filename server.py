import os
import sys
import socket
import select

import worker
from manager import Manager
from logger import Logger
from expiration import Expiration
from db import Db
from command import Command

class Server:

    def __init__(self, options):

        self.options = options.general
        self.running = True
        self.connections = {}

        # workers manager
        self.manager = Manager(self, self.options)
        self.manager.start()

        # expiration manager
        self.expiration = Expiration(options.expiration)
        self.expiration.start()
        
        # database manager
        self.db = Db(options.database)
        
        Command.register(self.shutdown, 'shutdown', 0, 'shutdown')


    def shutdown(self, args):
        self.stop()
        return Command.result(Command.RET_SUCCESS)

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

        except KeyboardInterrupt:
            Logger.debug('CTRL-C was pressed. Stopping server')

        except Exception as e:
            Logger.exception(str(e))

        self.stop()

        Logger.debug("shutting down network sockets")
        epoll.unregister(listener)
        epoll.close()
        sock.close()

        self.db.stop()
      
        self.manager.stop()

        self.expiration.stop()

        Logger.info("ItemReservation server ended")

       
