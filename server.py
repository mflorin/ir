import socket
import threading
import worker
import manager
import select

class Server:
    def __init__(self, options):
        self.options = options
        self.running = True
        self.manager = manager.Manager(self.options)
        self.manager.start()

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
        connections = {}

        try:
            while self.running:
                events = epoll.poll()
                for fd, event in events:

                    if fd == listener:
                        (clientsock, address) = sock.accept()
                        clientsock.setblocking(0)
                        fileno = clientsock.fileno()
                        epoll.register(fileno, select.EPOLLIN)
                        connections[fileno] = {'sock': clientsock, 'addr': address}
                    elif event & select.EPOLLIN:
                        if self.manager.dispatch(connections[fd]) != True:
                            """ Client closed connection """
                            connections[fileno]['sock'].shutdown(socket.SHUT_RDWR)
                            epoll.modify(fileno, 0)
                    elif event & select.EPOLLHUP:
                        epoll.unregister(fd)
                        addr = connections[fd]['addr']
                        print "closing " + addr[0] + ":" + str(addr[1])
                        connections[fd]['sock'].close()
                        del connections[fd]

        except KeyboardInterrupt:
            print "ctrlc"

        except:
            epoll.unregister(listener)
            epoll.close()
            sock.close()

        finally:
            epoll.unregister(listener)
            epoll.close()
            sock.close()
        
        self.manager.stop()
        self.manager.join()
