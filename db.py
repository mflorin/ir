"""
Implementation of database persistence using disk files
"""

import os
import sys
import threading
import cPickle
import time

from logger import Logger
from command import Command
from product import Product
from event import Event

class Db(threading.Thread):
    
    def __init__(self, options):

        super(Db, self).__init__()

        # application options
        self.options = options
        
        self.running = False

        # initialize the event object used for sleeping
        self.event = threading.Event()

        if self.options.persistence and os.path.exists(self.options.file_name):
            try:
                Logger.info('loading database from %s' % self.options.file_name)
                self.load()
            except Exception as e:
                Logger.critical(str(e))

        self.setup()

        # register our 'save' commands
        Command.register(self.saveCmd, 'save', 0, 'save')
        
        # treat reloadCfg
        Event.register('reload', self.reloadEvent)
        
    """
    start the thread
    """
    def start(self):
        if not self.running:
            Logger.info('starting the database manager')
            self.running = True
            super(Db, self).start()


    """
    stop the thread
    """
    def stop(self):
        if self.options.persistence:
            # save when stopping
            Logger.info('saving database to %s' % self.options.file_name)
            self.save()
        if self.running:
            Logger.info('stopping the database manager')
            self.running = False
            self.event.set()
            # in case of a reload, the event flag has to be clear
            # so that the next wait would actually wait
            self.event.clear()
            self.join()


    def setup(self):
        if self.options.persistence == True and len(self.options.file_name) > 0:
            if self.options.autosave_interval > 0:
                self.start()


    def reloadEvent(self, *args):
        self.stop()
        # we need this to start the thread again
        super(Db, self).__init__()
        self.setup()


    """
    periodic saves thread
    """
    def run(self):
        while self.running:
            self.event.wait(self.options.autosave_interval)
            try:
                Logger.info('saving database to %s' % self.options.file_name)
                self.save()
            except Exception as e:
                Logger.error("an error occured while trying to save the database to %s" % self.options.file_name)
                Logger.error(str(e))

    """
    Save the product data in the db

    @return True on success
    @return False on error
    """
    def save(self):

        data = {}

        # collect data from all modules
        Event.dispatch('db.save', data)
        
        # save data to the database
        f = open(self.options.file_name, 'wb')
        cPickle.dump(data, f, -1)
        f.close()

        del data


    """
    Load product data from the db

    @return True on success
    @return False on error
    """
    def load(self):
        f = open(self.options.file_name, 'rb')
        data = cPickle.load(f)
        f.close()
        Event.dispatch('db.load', data)
        del data
    
    
    """
    'save' command
    """
    def saveCmd(self, *args):
        if self.options.persistence:
            self.save()
            return Command.result(Command.RET_SUCCESS)
        else:
            return Command.result(Command.RET_ERR_GENERAL, 'database persistence is disabled')


       
