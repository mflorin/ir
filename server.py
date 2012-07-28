import os
import sys
import errno
import socket
import select
import importlib

import worker
from manager import Manager
from logger import Logger
from expiration import Expiration
from db import Db
from command import Command
from event import Event

class Server:

    def __init__(self, options):

        self.options = options.general
        self.running = True
        self.connections = {}
        self.modules = []

        # workers manager
        self.manager = Manager(self, self.options)
        self.manager.start()

        # expiration manager
        self.expiration = Expiration(options.expiration)
        self.expiration.start()
        
        # database manager
        self.db = Db(options.database)
        
        # load external modules
        self.loadModules()
       
        Event.register('reload', self.reloadEvent)
        
        Command.register(self.shutdown, 'shutdown', 0, 'shutdown')

    def reloadEvent(self, *args):
        self.loadModules()

    def loadModules(self):
        # load external modules
        for m in self.options.modules.split(','):
            m = m.strip()
            if len(m) == 0:
                continue
            if m in self.modules:
                continue
            try:
                Logger.debug('loading module ' + m)
                importlib.import_module(m)
                self.modules.append(m)
            except Exception as e:
                Logger.error('error while loading module ' + m)
                Logger.exception(str(e))


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

        while self.running:
            try:
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
                            try:
                                self.connections[fd]['sock'].shutdown(socket.SHUT_RDWR)
                                epoll.modify(fd, 0)
                            except:
                                pass

                    elif event & select.EPOLLHUP:
                        # socket shutdown
                        epoll.unregister(fd)
                        addr = self.connections[fd]['addr']
                        Logger.info(addr[0] + ":" + str(addr[1]) + " left")
                        self.connections[fd]['sock'].close()
                        del self.connections[fd]

            except KeyboardInterrupt:
                Logger.debug('CTRL-C was pressed. Stopping server')
                break

            except Exception as e:
                if e.args[0] in {errno.EINTR}:
                    # we do not want to exit because of SIGUSR1
                    # which is our reload signal
                    continue
                else:
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

       
