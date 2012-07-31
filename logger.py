import sys
import traceback
import logging

from event import Event
import config

class Logger:

    # logging object
    logger = None
     
    # logger options
    config = {}

    # file handler
    fh = None

    # console handler
    ch = None

    # logger default configuration values
    DEFAULTS = {
        'log_level': 'info',
        'log_file': '/var/log/motherbee/motherbee.log',
        'format': '[%(asctime)s](%(levelname)s) %(message)s'
    }

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
        Logger.logger = logging.getLogger(config.Config.APP_NAME)
        Logger.setup()
        Event.register('core.reload', Logger.reloadEvent)

    @staticmethod
    def loadConfig():
        Logger.config['log_level'] = config.Config.get('logger', 'log_level', Logger.DEFAULTS['log_level'])
        Logger.config['log_file'] = config.Config.get('logger', 'log_file', Logger.DEFAULTS['log_file'])
        Logger.config['format'] = config.Config.get('logger', 'format', Logger.DEFAULTS['format'])
        if Logger.config['log_level'] in Logger.LOG_LEVELS:
            Logger.config['log_level'] = Logger.LOG_LEVELS[Logger.config['log_level']]
        else:
            print 'Invalid log level `' + Logger.config['log_level'] + '`'
            print 'Falling back to log level ' + Logger.DEFAULTS['log_level']
            Logger.config['log_level'] = Logger.LOG_LEVELS[Logger.DEFAULTS['log_level']]


    @staticmethod
    def setup():
        Logger.loadConfig()
        if Logger.fh:
            Logger.logger.removeHandler(Logger.fh)
            del Logger.fh
            Logger.fh = None

        if Logger.ch:
            Logger.logger.removeHandler(Logger.ch)
            del Logger.ch
            Logger.ch = None

        Logger.logger.setLevel(Logger.config['log_level'])
        Logger.fh = logging.FileHandler(Logger.config['log_file'])
        Logger.fh.setLevel(Logger.config['log_level'])
        Logger.fh.setFormatter(logging.Formatter(Logger.config['format']))
        Logger.logger.addHandler(Logger.fh)

        if config.Config.general.debug:
            # add console logging
            Logger.ch = logging.StreamHandler()
            Logger.ch.setLevel(Logger.config['log_level'])
            Logger.ch.setFormatter(logging.Formatter(Logger.config['format']))
            Logger.logger.addHandler(Logger.ch)
     

    @staticmethod
    def reloadEvent(*args):
        Logger.setup()

    @staticmethod
    def debug(*args):
        Logger.logger.debug(args[0])

    @staticmethod
    def info(*args):
        Logger.logger.info(args[0])

    @staticmethod
    def warn(*args):
        Logger.logger.warn(args[0])

    @staticmethod
    def error(*args):
        Logger.logger.error(args[0])

    @staticmethod
    def critical(*args):
        Logger.logger.critical(args[0])

    @staticmethod
    def exception(*args):
        Logger.warn(traceback.format_exc())
        if args and len(args) > 0:
            Logger.warn(args[0])

    @staticmethod
    def marker():
        Logger.debug('--- marker ---')

