import socket
import threading
import Queue

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
        cmd = job['cmd']

        print "Got " + cmd + " from " + addr[0] + ":" + str(addr[1])

    def run(self):
        while not self.queue.empty():
            self.doJob(self.queue.get())
            self.queue.task_done()

        self.queue.join()
        self.manager.notifyJoin(self)
