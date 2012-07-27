#!/usr/bin/python

import sys
import server
import argparse
import os
import ConfigParser
import socket
import logging
from logger import Logger

VERSION = "1.0.0"

DEFAULT_CONFIG_FILE = '/etc/itemreservation/itemreservation.conf'
DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 2000
DEFAULT_WORKERS = 500
DEFAULT_LOG_LEVEL = 'warning'
DEFAULT_LOG_FILE = '/var/log/ir/ir.log'
DEFAULT_BACKLOG = 0
DEFAULT_DEBUG = False
DEFAULT_TTL = 300
DEFAULT_CLEANUP_INTERVAL = 10

# used when parsing the log level from the
# configuration file into a logging module level
log_levels = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARN,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}


class Options(object):
    pass

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description='Item Reservation Server', 
        prog='ItemReservation'
    )

    parser.add_argument('-f', '--file', 
        default=DEFAULT_CONFIG_FILE, 
        help="configuration file")

    parser.add_argument('-d', '--debug',
        default = DEFAULT_DEBUG,
        action='store_true',
        help="run in console, don't detach")

    parser.add_argument('--version', 
        action='version', 
        version='%(prog)s ' + str(VERSION))

    try:
        parser.parse_args(sys.argv[1:], namespace = Options)
    except:
        sys.exit(1)

    if Options.file:
        config = ConfigParser.SafeConfigParser(defaults = {
            'host': str(DEFAULT_HOST),
            'port': str(DEFAULT_PORT),
            'workers': str(DEFAULT_WORKERS),
            'log_level': str(DEFAULT_LOG_LEVEL),
            'log_FILE': str(DEFAULT_LOG_FILE),
            'backlog': str(DEFAULT_BACKLOG),
        })

        try:
            config.read(Options.file)
            Options.host = config.get('general', 'host') if config.has_option('general', 'host') else DEFAULT_HOST
            Options.port = config.getint('general', 'port') if config.has_option('general', 'port') else DEFAULT_PORT
            Options.workers = config.getint('general', 'workers') if config.has_option('general', 'workers') else DEFAULT_WORKERS
            Options.log_level = config.get('general', 'log_level') if config.has_option('general', 'log_level') else DEFAULT_LOG_LEVEL
            Options.log_file = config.get('general', 'log_file') if config.has_option('general', 'log_file') else DEFAULT_LOG_FILE
            Options.backlog = config.getint('general', 'backlog') if config.has_option('general', 'backlog') else DEFAULT_BACKLOG
            Options.ttl = config.getint('general', 'ttl') if config.has_option('general', 'ttl') else DEFAULT_TTL
            Options.cleanup_interval = config.getint('general', 'cleanup_interval') if config.has_option('general', 'cleanup_interval') else DEFAULT_CLEANUP_INTERVAL

            if Options.backlog <= 0:
                Options.backlog = socket.SOMAXCONN
        
        except:
            print "An error was encountered when parsing " + Options.file
            print sys.exc_info()[1]
            sys.exit(1)

    if Options.log_level in log_levels:
        Options.log_level = log_levels[Options.log_level]
    else:
        print 'Invalid log level `' + Options.log_level + '`'
        print 'Falling back to log level ' + DEFAULT_LOG_LEVEL
        Options.log_level = log_levels[DEFAULT_LOG_LEVEL]

    Logger.init(Options)

    if Options.debug:
        # add console logging
        ch = logging.StreamHandler()
        ch.setLevel(Options.log_level)
        ch.setFormatter(Logger.getFormatter())
        Logger.logger.addHandler(ch)

    # interval to run the cleanup
    Options.cleanup_interval = DEFAULT_CLEANUP_INTERVAL
    Options.ttl = DEFAULT_TTL

    if not Options.debug:
        pid = os.fork()
        if pid == 0:
            server.Server(Options).run()
        else:
            sys.exit(0)
    else:
        server.Server(Options).run()
