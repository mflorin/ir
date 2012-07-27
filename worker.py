import socket
import threading
import Queue
import re
import sys
import command
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
        cmd = job['cmd'].strip()
        Logger.debug(cmd)
        for c in cmd.split("\n"):
            c = c.strip()
            try:
                res = command.Command.processCmd(re.compile("\s").split(c)) + "\r\n"
            except:
                Logger.exception(sys.exc_info()[1])
                continue

            try:
                sock.send(res)
            except:
                Logger.warn("client " + addr[0] + ":" + str(addr[1]) + " probably left while trying to send response for command `" + c + "`")
                Logger.warn(sys.exc_info()[1])
                continue
            

    def run(self):
        while not self.queue.empty():
            self.doJob(self.queue.get())
            self.queue.task_done()

        self.queue.join()
        self.manager.notifyJoin(self)
