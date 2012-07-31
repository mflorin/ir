import os
import sys
import errno
import socket
import select

import worker
from manager import Manager
from logger import Logger
from db import Db
from command import Command
from event import Event
from config import Config

class Server:

    # default configuration values
    DEFAULTS = {
        'server_name': Config.APP_NAME,
        'file': '/etc/motherbee/motherbee.conf',
        'host': '0.0.0.0',
        'port': 2000,
        'backlog': 0,
    } 

    def __init__(self):

        self.config = {}

        # load configuration options
        self.loadConfig()

        self.running = True
        self.connections = {}

        # initialize the epoll object
        self.epoll = select.epoll()

        # workers manager
        self.manager = Manager(self)
        self.manager.start()
     
        # database manager
        self.db = Db()
        
        Event.register('core.reload', self.reloadEvent)
        
        Command.register(self.shutdownCmd, 'core.shutdown', 0, 'core.shutdown')

    def loadConfig(self):
        self.config['server_name'] = Config.get('general', 'server_name', Server.DEFAULTS['server_name'])
        self.config['modules'] = Config.get('general', 'modules')
        self.config['host'] = Config.get('general', 'host', Server.DEFAULTS['host'])
        self.config['port'] = Config.getint('general', 'port', Server.DEFAULTS['port'])
        self.config['backlog'] = Config.getint('general', 'backlog', Server.DEFAULTS['backlog']) 
        if self.config['backlog'] <= 0:
            self.config['backlog'] = socket.SOMAXCONN
 

    def reloadEvent(self, *args):
        self.loadConfig()

    def shutdownCmd(self, args):
        self.stop()
        return Command.result(Command.RET_SUCCESS)

    def stop(self):
        self.running = False

    def closeConnection(self, fd):
        self.epoll.unregister(fd)
        addr = self.connections[fd]['addr']
        Logger.info(addr[0] + ":" + str(addr[1]) + " left")
        self.connections[fd]['sock'].close()
        del self.connections[fd]


    def run(self):

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.config['host'], self.config['port']))
        sock.listen(self.config['backlog'])
        sock.setblocking(0)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        listener = sock.fileno()
        self.epoll.register(listener, select.EPOLLIN | select.EPOLLOUT | select.EPOLLHUP)

        Logger.info("%s server started" % self.config['server_name'])

        while self.running:
            try:
                events = self.epoll.poll()
                for fd, event in events:

                    if fd == listener:
                        # New connection
                        (clientsock, address) = sock.accept()
                        clientsock.setblocking(0)
                        fileno = clientsock.fileno()
                        self.epoll.register(fileno, select.EPOLLIN)
                        self.connections[fileno] = {
                            'sock': clientsock, 
                            'addr': address
                        }
                    elif event & select.EPOLLIN:
                        # incoming data from client
                        if self.manager.dispatch(self.connections[fd]) != True:
                            # Client closed connection
                            try:
                                self.closeConnection(fd)
                            except:
                                pass

                    elif event & select.EPOLLHUP:
                        # socket shutdown
                        self.closeConnection(fd)

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


#        self.stop()
        
        # dispatching shutdown to all modules
        Event.dispatch('core.shutdown')

        Logger.debug("shutting down network sockets")
        self.epoll.unregister(listener)
        self.epoll.close()
        sock.close()

        self.db.stop()
      
        self.manager.stop()

        Logger.info("%s server ended" % self.config['server_name'])

       
