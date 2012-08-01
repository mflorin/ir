import sys
import socket
import signal
import logging
import ConfigParser

from command import Command
from event import Event

class Config(object):
    
    # ConfigParser object
    config = None

    # application name
    APP_NAME = 'MotherBee'

    class general(object):
        file = '/etc/motherbee/motherbee.conf'
        debug = False
        pass
   
    @staticmethod
    def init():

        Config.load()

        # register our "reloadCfg" command
        Command.register(Config.reloadCmd, 'config.reload', 0, 'config.reload')
        
        # reload config when receiving SIGUSR1
        signal.signal(signal.SIGUSR1, Config.sigusr1)


    @staticmethod
    def sigusr1(sig, frame):
        Config.reload()

    @staticmethod
    def load():

        if Config.general.file:
            Config.config = ConfigParser.RawConfigParser()
            try:
                Config.config.read(Config.general.file)
            except:
                print "An error was encountered when parsing " + Config.general.file
                print sys.exc_info()[1]
                sys.exit(1)


    @staticmethod
    def reload():
        Config.load()
        Event.dispatch('core.reload', None)

    @staticmethod
    def reloadCmd(args):
        Config.reload()
        return Command.result(Command.RET_SUCCESS)

    @staticmethod
    def get(section, option, default=None):
        return Config.config.get(section,option) if Config.config.has_option(section, option) else default

    @staticmethod
    def getint(section, option, default=None):
        return Config.config.getint(section,option) if Config.config.has_option(section, option) else default

    @staticmethod
    def getfloat(section, option, default=None):
        return Config.config.getfloat(section,option) if Config.config.has_option(section, option) else default

    @staticmethod
    def getboolean(section, option, default=False):
        return Config.config.getboolean(section,option) if Config.config.has_option(section, option) else default
