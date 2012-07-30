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

        # condition variable
        self.event = threading.Event()

        # flag indicating that we're still running
        self.running = False
        
        # application options
        self.options = options 

        # available idle threads
        self.idleWorkers = Queue.Queue()

        # read buffer to collect data from sockets
        # and split it later by \n and feed it to workers
        # when a \n is met
        # fd -> buffer
        self.readBuffer = {}
   
        # register commands
        Command.register(self.workersCmd, 'workers', 0)
        
        # server instance
        self.server = server

    def idleWorkerPush(self, w):
        self.idleWorkers.put(w)

    def idleWorkerPop(self):
        ret = None
        if not self.idleWorkers.empty():
            try:
                ret = self.idleWorkers.get_nowait()
            except:
                Logger.exception()

        if ret:
            Logger.info('worker %d popped' % ret.ident)
            self.idleWorkers.task_done()
        return ret

    """
    pick a worker, either from the idle workers queue or
    by creating one or by computing the worker with the
    smallest job queue
    """
    def pickWorkerUnlocked(self):

        # try to pick an idle worker
        ret = self.idleWorkerPop()
        if ret:
            return ret

        # try to start a new worker
        if len(self.workers) < self.options.workers:
            ret = None
            try:
                ret = self.createWorker()
                ret.start()
                return ret
            except Exception as e:
                Logger.exception()
                if ret:
                    self.removeWorkerUnlocked(ret)
                    del ret
                    ret = None

        # try to pick the least busy worker
        _min = -1
        for w in self.workers:
            # compute the worker with the smallest
            # queue and add the job to it
            _size = w.getQSize()
            if (_size < _min or _min == -1):
                ret = w
                _min = _size

        return ret

    """
    read bytes from the socket and try to split them
    into commands which will be feeded to the workers
    """
    def dispatch(self, conn):

        processed = False
        sock = conn['sock']
        addr = conn['addr']

        cmd = None
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

        _served = False
        # pick a worker to assign the job to
        try:
            w = self.pickWorkerUnlocked()
            if w:
                w.addJob(job)
                _served = True
        except:
            Logger.exception()

        if _served == False:
            Logger.warn("Connection from " + addr[0] + ":" + str(addr[1]) + " was dropped")

        self.workersLock.release()

        return True

        
    def createWorker(self):
        w = worker.Worker(self, self.options)
        Logger.info('adding worker')
        self.addWorkerUnlocked(w)
        return w

    def addWorkerUnlocked(self, w):
        self.workers.append(w)

    def removeWorkerUnlocked(self, w):
        Logger.info('removing worker %d' % w.ident)
        self.workers.remove(w)

    """ scale down method; this method's main purpose is to join
    idle worker threads from time to time """
    def run(self):
        while self.running:

            self.event.wait(self.options.scale_down_interval)

            self.workersLock.acquire()

            Logger.debug('scaling down started')
            
            while not self.idleWorkers.empty():
                i = self.idleWorkers.get()
                i.stop()
                Logger.info('removing %d' % i.ident)
                self.removeWorkerUnlocked(i)
                self.idleWorkers.task_done()

            self.idleWorkers.join()

            Logger.debug('scaling down ended')

            self.workersLock.release()

            self.event.clear()

        # shut down remaining workers, dropping
        # unprocessed commands
        self.shutdownWorkers()

    def shutdownWorkers(self):
        # we don't need to lock here since
        # we know we're running unlocked
        for w in self.workers:

            # WARNING: unprocessed commands are dropped
            w.emptyQueue()

            w.stop()
            self.removeWorkerUnlocked(w)


    def start(self):
        Logger.info('starging the workers manager')
        self.running = True
        super(Manager, self).start()


    def stop(self):
        Logger.info('stopping the workers manager')
        self.running = False
        self.event.set()
        self.join()


    def workersCmd(self, args):
        return Command.result(Command.RET_SUCCESS, {'active': len(self.workers), 'max': self.options.workers})

