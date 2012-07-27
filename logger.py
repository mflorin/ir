import logging

class Logger:
    # setting up the logger
    logger = logging.getLogger('ir')
    formatter = logging.Formatter('[%(asctime)s](%(levelname)s) %(message)s')

    @staticmethod
    def init(Options):
        Logger.logger.setLevel(Options.log_level)
        fh = logging.FileHandler(Options.log_file)
        fh.setLevel(Options.log_level)
        fh.setFormatter(Logger.formatter)
        Logger.logger.addHandler(fh)

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
        Logger.logger.warn(args[0])

    @staticmethod
    def marker():
        Logger.debug('--- marker ---')

