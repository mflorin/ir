import socket
import threading
import Queue
import re
import sys

from command import Command
from logger import Logger

class Worker(threading.Thread):

    def __init__(self, manager, options):
        super(Worker, self).__init__()
        self.event = threading.Event()
        self.running = False
        self.daemon = True
        self.manager = manager
        self.options = options
        self.queue = Queue.Queue()

    def addJob(self, job):
        self.queue.put(job)
        self.event.set()

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

    def getQSize(self):
        return self.queue.qsize()

    def emptyQueue(self):
        while not self.queue.empty():
            self.queue.get_nowait()
            self.queue.task_done()
        
    def isIdle(self):
        return self.queue.empty()

    def run(self):
        while self.running:
            self.event.wait()
            while not self.queue.empty():
                self.doJob(self.queue.get())
                self.queue.task_done()
            self.queue.join()
            if self.running:
                # do not add ourselves to the idle queue
                # if stop() was called, otherwise we'll 
                # end up adding ourselves to the queue
                # right after we were stopped by the
                # scale_down thread
                self.manager.idleWorkerPush(self)
            self.event.clear()

    def start(self):
        if not self.running:
            self.running = True
            super(Worker, self).start()

    def stop(self):
        if self.running:
            self.running = False
            self.event.set()
            self.join()
        return True
