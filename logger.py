import sys
import traceback
import logging

from event import Event

class Logger:
    # setting up the logger
    logger = logging.getLogger('ir')
    formatter = logging.Formatter('[%(asctime)s](%(levelname)s) %(message)s')
    options = None
    fh = None

    @staticmethod
    def init(options):
        Logger.options = options
        Logger.setup()
        Event.register('reload', Logger.reload)

    @staticmethod
    def setup():
        if Logger.fh:
            Logger.logger.removeHandler(Logger.fh)

        Logger.logger.setLevel(Logger.options.log_level)
        Logger.fh = logging.FileHandler(Logger.options.log_file)
        Logger.fh.setLevel(Logger.options.log_level)
        Logger.fh.setFormatter(Logger.formatter)
        Logger.logger.addHandler(Logger.fh)

    @staticmethod
    def reload(*args):
        Logger.setup()

    @staticmethod
    def getFormatter():
        return Logger.formatter

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

