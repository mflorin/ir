"""
Implementation of database persistence using disk files
"""

import os
import sys
import threading
import cPickle
import time

from config import Config
from logger import Logger
from command import Command
from event import Event

class Db(threading.Thread):

    DEFAULTS = {
        'persistence': False,
        'file': '/var/lib/motherbee/motherbee.db',
        'autosave_interval': 60
    }
  
    def __init__(self):

        super(Db, self).__init__()

        # config options
        self.config = {}

        self.loadConfig()
        
        self.running = False

        # initialize the event object used for sleeping
        self.event = threading.Event()

        if self.config['persistence'] and os.path.exists(self.config['file_name']):
            try:
                Logger.info('loading database from %s' % self.config['file_name'])
                self.load()
            except Exception as e:
                Logger.critical(str(e))

        self.setup()

        # register our 'save' commands
        Command.register(self.saveCmd, 'db.save', 0, 'db.save')
        
        # treat reloadCfg
        Event.register('core.reload', self.reloadEvent)

    def loadConfig(self):
        self.config['persistence'] = Config.getboolean('database', 'persistence', Db.DEFAULTS['persistence']) 
        self.config['file_name'] = Config.get('database', 'file', Db.DEFAULTS['file'])
        self.config['autosave_interval'] = Config.getint('database', 'autosave_interval', Db.DEFAULTS['autosave_interval'])
  
        
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
        if self.config['persistence']:
            # save when stopping
            Logger.info('saving database to %s' % self.config['file_name'])
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
        if self.config['persistence'] == True and len(self.config['file_name']) > 0:
            if self.config['autosave_interval'] > 0:
                self.start()


    def reloadEvent(self, *args):
        self.stop()
        # we need this to start the thread again
        super(Db, self).__init__()
        self.loadConfig()
        self.setup()


    """
    periodic saves thread
    """
    def run(self):
        while self.running:
            self.event.wait(self.config['autosave_interval'])
            try:
                Logger.info('saving database to %s' % self.config['file_name'])
                self.save()
            except Exception as e:
                Logger.error("an error occured while trying to save the database to %s" % self.config['file_name'])
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
        f = open(self.config['file_name'], 'wb')
        cPickle.dump(data, f, -1)
        f.close()

        del data


    """
    Load product data from the db

    @return True on success
    @return False on error
    """
    def load(self):
        f = open(self.config['file_name'], 'rb')
        data = cPickle.load(f)
        f.close()
        Event.dispatch('db.load', data)
        del data
    
    
    """
    'save' command
    """
    def saveCmd(self, *args):
        if self.config['persistence']:
            self.save()
            return Command.result(Command.RET_SUCCESS)
        else:
            return Command.result(Command.RET_ERR_GENERAL, 'database persistence is disabled')


       
