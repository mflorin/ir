import sys
import socket
import signal
import logging
import ConfigParser

from command import Command
from event import Event

class Options(object):
    
    DEFAULT_LOG_LEVEL = 'info'

    class general(object):
        file = '/etc/itemreservation/itemreservation.conf'
        host = '0.0.0.0'
        port = 2000
        workers = 500
        backlog = 0
        debug = False
        pass

    class logger(object):
        log_level = 'warning'
        log_file = '/var/log/ir/ir.log'
        pass

    class expiration(object):
        ttl = 300
        cleanup_interval = 10
        pass

    class database(object):
        persistence = False
        file_name = '/var/lib/ir/ir.db'
        autosave_interval = 0
    
    # used when parsing the log level from the
    # configuration file into a logging module level
    LOG_LEVELS = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARN,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
    }

    @staticmethod
    def init():
        # register our "reloadCfg" command
        Command.register(Options.reloadCfgCmd, 'reloadCfg', 0, 'reloadCfg')

    @staticmethod
    def load():

        if Options.general.file:
            config = ConfigParser.SafeConfigParser(defaults = {
                'host': str(Options.general.host),
                'port': str(Options.general.port),
                'workers': str(Options.general.workers),
                'backlog': str(Options.general.backlog),
                'log_level': str(Options.logger.log_level),
                'log_file': str(Options.logger.log_file),
                'ttl': str(Options.expiration.ttl),
                'cleanup_interval': str(Options.expiration.cleanup_interval),
                'persistence': 'yes' if Options.database.persistence else 'no',
                'file': Options.database.file_name,
                'autosave_interval': str(Options.database.autosave_interval)
            })

            try:
                config.read(Options.general.file)
                Options.general.host = config.get('general', 'host')
                Options.general.port = config.getint('general', 'port')
                Options.general.workers = config.getint('general', 'workers')
                Options.general.backlog = config.getint('general', 'backlog') 
                Options.logger.log_level = config.get('logger', 'log_level') 
                Options.logger.log_file = config.get('logger', 'log_file')
                Options.expiration.ttl = config.getint('expiration', 'ttl')
                Options.expiration.cleanup_interval = config.getint('expiration', 'cleanup_interval') 
                Options.database.persistence = config.getboolean('database', 'persistence') 
                Options.database.file_name = config.get('database', 'file') 
                Options.database.autosave_interval = config.getint('database', 'autosave_interval') 

                if Options.general.backlog <= 0:
                    Options.general.backlog = socket.SOMAXCONN
           
                if Options.logger.log_level in Options.LOG_LEVELS:
                    Options.logger.log_level = Options.LOG_LEVELS[Options.logger.log_level]
                else:
                    print 'Invalid log level `' + Options.logger.log_level + '`'
                    print 'Falling back to log level ' + Options.DEFAULT_LOG_LEVEL
                    Options.logger.log_level = Options.LOG_LEVELS[DEFAULT_LOG_LEVEL]

            except:
                print "An error was encountered when parsing " + Options.general.file
                print sys.exc_info()[1]
                sys.exit(1)

    @staticmethod
    def reload():
        Options.load()
        Event.dispatch('reload')

    @staticmethod
    def reloadCfgCmd(args):
        Options.reload()
        return Command.result(Command.RET_SUCCESS)
