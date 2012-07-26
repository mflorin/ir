import threading
import worker
import socket
import errno
import Queue

class Manager(threading.Thread):
    def __init__(self, options):

        threading.Thread.__init__(self)

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
            return False
        

        job = {'sock': sock, 'addr': addr, 'cmd': cmd}
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
            print "Connection from " + addr[0] + ":" + str(addr[1]) + " was dropped"
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
        if worker:
            self.joinable.put(worker)
            self.removeWorker(worker)

        # notify so that run()
        # can go on joining what's in the 
        # joinable queue
        self.workersCond.acquire()
        self.workersCond.notify()
        self.workersCond.release()

    """ this method's main purpose is to join
    worker threads from the joinable queue """
    def run(self):
        while self.running:

            self.workersCond.acquire()

            # wait for the signal
            self.workersCond.wait()

            while not self.joinable.empty():
                w = self.joinable.get()
                w.join()
                self.joinable.task_done()

            self.workersCond.release()

        self.joinable.join()

    def stop(self):
        self.running = False
        self.notifyJoin()

