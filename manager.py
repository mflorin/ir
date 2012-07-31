import threading
import worker
import socket
import errno
import Queue
import inspect
import sys

from command import Command
from logger import Logger
from config import Config
from event import Event

class Manager(threading.Thread):

    # 1M buffer size
    MAX_BUFFER_SIZE = 1048576

    # default configuration values
    DEFAULTS = {
        'workers': 500,
        'scale_down_interval': 60
    }

    def __init__(self, server):

        super(Manager, self).__init__()

        # list of workers
        self.workers = []

        # mutex for the list of workers
        self.workersLock = threading.RLock()

        # condition variable
        self.event = threading.Event()

        # flag indicating that we're still running
        self.running = False
        
        # manager config
        self.config = {}
        self.loadConfig()

        # available idle threads
        self.idleWorkers = Queue.Queue()

        # read buffer to collect data from sockets
        # and split it later by \n and feed it to workers
        # when a \n is met
        # fd -> buffer
        self.readBuffer = {}
   
        # register commands
        Command.register(self.workersCmd, 'core.workers', 0)

        # register for the core.reload event
        Event.register('core.reload', self.reloadEvent)
                
        # server instance
        self.server = server


    def loadConfig(self):
        self.config['workers'] = Config.getint('general', 'workers', Manager.DEFAULTS['workers'])
        self.config['scale_down_interval'] = Config.getint('general', 'scale_down_interval', Manager.DEFAULTS['scale_down_interval'])
       

    def reloadEvent(self):
        self.loadConfig()

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
        if len(self.workers) < self.config['workers']:
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
        lastcmd = cmds[len(cmds) - 1]
        self.readBuffer[fd] = lastcmd

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
        w = worker.Worker(self)
        self.addWorkerUnlocked(w)
        return w

    def addWorkerUnlocked(self, w):
        self.workers.append(w)

    def removeWorkerUnlocked(self, w):
        self.workers.remove(w)

    """ scale down method; this method's main purpose is to join
    idle worker threads from time to time """
    def run(self):
        while self.running:

            self.event.wait(self.config['scale_down_interval'])

            self.workersLock.acquire()

            while not self.idleWorkers.empty():
                i = self.idleWorkers.get()
                i.stop()
                self.removeWorkerUnlocked(i)
                self.idleWorkers.task_done()

            self.idleWorkers.join()

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
        Logger.info('starting the workers manager')
        self.running = True
        super(Manager, self).start()


    def stop(self):
        Logger.info('stopping the workers manager')
        self.running = False
        self.event.set()
        self.join()


    def workersCmd(self, args):
        return Command.result(Command.RET_SUCCESS, {'active': len(self.workers), 'max': self.config['workers']})

