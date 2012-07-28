"""
Implementation of database persistence using disk files
"""

import threading
import cPickle
import time
import sys

from logger import Logger
from command import Command
from product import Product

class Db(threading.Thread):
    
    def __init__(self, filename, interval):

        super(Db, self).__init__()

        self.filename = filename
        self.interval = interval
        self.running = True

        # initialize the event object used for sleeping
        self.event = threading.Event()

        # register our 'save' commands
        Command.register(self.saveCmd, 'save', 0, 'save')

    """
    periodic saves thread
    """
    def run(self):
        while self.running:
            self.event.wait(self.interval)
            Logger.info("saving database to %s" % self.filename)
            self.save()

    """
    stop the thread
    """
    def stop(self):
        self.running = False
        if self.interval > 0:
            self.event.set()
            self.join()

    """
    Save the product data in the db

    @return True on success
    @return False on error
    """
    def save(self):
        f = open(self.filename, 'wb')
        cPickle.dump(Product.prepareDbData(), f, -1)
        f.close()

    """
    Load product data from the db

    @return True on success
    @return False on error
    """
    def load(self):
        f = open(self.filename, 'rb')
        Product.loadDbData(cPickle.load(f))
        f.close()
    
    
    """
    'save' command
    """
    def saveCmd(self, *args):
        self.save()
        return Command.result(Command.RET_SUCCESS)

   
