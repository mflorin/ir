import threading
import worker

class Manager(threading.Thread):
    def __init__(self, options):

        threading.Thread.__init__(self)

        """ list of workers """
        self.workers = []

        """ mutex for the list of workers """
        self.workersLock = threading.RLock()

        """ condition variable indicating that a thread 
        finished and should be joined """
        self.workersCond = threading.Condition()

        """ flag indicating that we're still running """
        self.running = True
        
        """ application options """
        self.options = options 

   
    def dispatch(self, conn):
        processed = False
        sock = conn['sock']
        addr = conn['addr']
        cmd = sock.recv(1024)
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
            print "Connection from " + addr[0] + ":" + str(addr[1]) + " dropped"
        
    def createWorker(self):
        w = worker.Worker(self, self.options)
        self.addWorker(w)
        return w

    def addWorker(self, w):
        self.workersLock.acquire()
        self.workers.append(w)
        self.workersLock.release()

    def removeWorker(self, w):
        self.workersLock.acquire()
        self.workers.remove(w)
        self.workersLock.release()

    def notifyJoin(self):
        self.workersCond.acquire()
        self.workersCond.notify()
        self.workersCond.release()

    def run(self):
        while self.running:
            self.workersCond.acquire()
            self.workersCond.wait()
            self.workersLock.acquire()
            for w in self.workers:
                w.join(.2)
                if not w.isAlive():
                    print str(w.ident) + " joined"
                    self.workers.remove(w)

            self.workersLock.release()

            self.workersCond.release()
    
    def stop(self):
        self.running = False
        self.notifyJoin()

