import socket
import threading
import Queue
import re
import sys

from command import Command
from logger import Logger

class Worker(threading.Thread):

    def __init__(self, manager, options):
        threading.Thread.__init__(self)
        self.daemon = True
        self.manager = manager
        self.options = options
        self.queue = Queue.Queue()

    def isAvailable(self):
        return not self.queue.full()

    def addJob(self, job):
        self.queue.put(job)

    def doJob(self, job):

        sock = job['sock']
        addr = job['addr']
        cmds = job['commands']
        socket_ok = True
        for c in cmds:
            c = c.strip()
            try:
                res = Command.processCmd(re.compile("\s").split(c)) + "\r\n"
            except:
                Logger.exception()
                continue

            try:
                if socket_ok:
                    if sock.fileno() in self.manager.server.connections:
                        # send the response only if we still have 
                        # someone to talk to
                        sock.send(res)
                    else:
                        socket_ok = False
                        Logger.info("client " + addr[0] + ":" + str(addr[1]) + " left while trying to send response for command `" + c + "`")

            except:
                socket_ok = False
                Logger.warn("client " + addr[0] + ":" + str(addr[1]) + " left while trying to send response for command `" + c + "`")
                # we're not going to insist on writing to a broken socket

    def run(self):
        while not self.queue.empty():
            self.doJob(self.queue.get())
            self.queue.task_done()

        self.queue.join()
        self.manager.notifyJoin(self)
