import threading
import worker
import socket
import errno
import Queue
import inspect
import sys

from command import Command
from logger import Logger

class Manager(threading.Thread):

    # 1M buffer size
    MAX_BUFFER_SIZE = 1048576

    def __init__(self, server, options):

        super(Manager, self).__init__()

        # list of workers
        self.workers = []

        # mutex for the list of workers
        self.workersLock = threading.RLock()

        # condition variable indicating that a thread 
        # finished and should be joined
        self.workersCond = threading.Condition()

        # flag indicating that we're still running
        self.running = True
        
        # application options
        self.options = options 

        # joinable threads queue
        self.joinable = Queue.Queue()

        # read buffer to collect data from sockets
        # and split it later by \n and feed it to workers
        # when a \n is met
        # fd -> buffer
        self.readBuffer = {}
   
        # register commands
        Command.register(self.workersCmd, 'workers', 0)
        
        # server instance
        self.server = server

    """
    read bytes from the socket and try to split them
    into commands which will be feeded to the workers
    """
    def dispatch(self, conn):

        processed = False
        sock = conn['sock']
        addr = conn['addr']

        while True:
            try:
                cmd = sock.recv(1024)
            except socket.error, e:
                if e.args[0] in { errno.EINTR, errno.EAGAIN, errno.EWOULDBLOCK }:
                    # retry on eintr, eagain and ewouldblock
                    continue
            break

        if not cmd or len(cmd) == 0:
            # client closed the connection
            Logger.debug("0 bytes read from " + addr[0] + ":" + str(addr[1]))
            return False

        fd = sock.fileno()
        if fd not in self.readBuffer:
            self.readBuffer[fd] = ""

        self.readBuffer[fd] += cmd

        if not Command.SEPARATOR in self.readBuffer[fd]:
            if len(self.readBuffer[fd]) > Manager.MAX_BUFFER_SIZE:
                self.readBuffer[fd] = ""
            return True

        # split the buffer into commands and feed the workers
        cmds = self.readBuffer[fd].split(Command.SEPARATOR)
        
        # retain the last partial command if any
        lastcmd = cmds[len(cmds) - 1].strip()
        if len(lastcmd) > 0:
            self.readBuffer[fd] = lastcmd
        else:
            self.readBuffer[fd] = ""

        del cmds[len(cmds) - 1]

        job = {'sock': sock, 'addr': addr, 'commands': cmds}
        self.workersLock.acquire()
        if len(self.workers) < self.options.workers:
            w = self.createWorker()
            w.addJob(job)
            w.start()
            processed = True
        else:
            for w in self.workers:
                if (w.isAvailable()):
                    w.addJob(job)
                    processed = True
                    break
        self.workersLock.release()
        if not processed:
            logger.warn("Connection from " + addr[0] + ":" + str(addr[1]) + " was dropped")
            return False
        else:
            return True

        
    def createWorker(self):
        w = worker.Worker(self, self.options)
        self.addWorker(w)
        return w

    def addWorker(self, w):
        self.workers.append(w)

    def removeWorker(self, w):
        # we're locking here because we don't
        # want to end up using this worker in dispatch()
        self.workersLock.acquire()
        self.workers.remove(w)
        self.workersLock.release()

    def notifyJoin(self, worker = None):
        # notify so that run()
        # can go on joining what's in the 
        # joinable queue
        self.workersCond.acquire()

        if worker:
            # it's essential to push the worker
            # in the joinable queue AFTER acquiring
            # the lock, otherwise we'll end up in
            # a deadlock where the manager is
            # fetching this fresh worker from the queue
            # and gets blocked in join because the worker
            # is holding the workersCond lock waiting
            # for the manager to release it :)
            self.joinable.put(worker)
            self.removeWorker(worker)

        self.workersCond.notify()
        self.workersCond.release()

    """ this method's main purpose is to join
    worker threads from the joinable queue """
    def run(self):
        while self.running:

            self.workersCond.acquire()

            # wait for the signal
            self.workersCond.wait()
            
            try:
                while not self.joinable.empty():
                    try:
                        w = self.joinable.get()
                        w.join()
                        self.joinable.task_done()
                    except:
                        Logger.exception()
                        continue
            except:
                Logger.exception()

            self.workersCond.release()

        self.joinable.join()

    def start(self):
        Logger.info('starging the workers manager')
        super(Manager, self).start()

    def stop(self):
        Logger.info('stopping the workers manager')
        self.running = False
        self.notifyJoin()
        self.join()


    def workersCmd(self, args):
        return Command.result(Command.RET_SUCCESS, {'active': len(self.workers), 'max': self.options.workers})

