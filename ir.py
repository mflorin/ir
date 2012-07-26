#!/usr/bin/python

import sys
import server
import argparse
import os
import ConfigParser
import socket
import logging

DEFAULT_CONFIG_FILE = '/etc/itemreservation/itemreservation.conf'
DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 2000
DEFAULT_WORKERS = 500
DEFAULT_LOG_LEVEL = 'warning'
DEFAULT_BACKLOG = socket.SOMAXCONN
DEFAULT_DEBUG = False

VERSION = "1.0.0"

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

    parser.add_argument('--version', 
        action='version', 
        version='%(prog)s ' + str(VERSION))

    try:
        parser.parse_args(sys.argv[1:], namespace = Options)
    except:
        print "error: " + sys.exc_info()[0]
        sys.exit(1)

    if Options.file:
        config = ConfigParser.SafeConfigParser(defaults = {
            'host': str(DEFAULT_HOST),
            'port': str(DEFAULT_PORT),
            'workers': str(DEFAULT_WORKERS),
            'log_level': str(DEFAULT_LOG_LEVEL),
            'backlog': str(DEFAULT_BACKLOG),
            'debug': str(DEFAULT_DEBUG)
        })

        try:
            config.read(Options.file)
            Options.host = config.get('general', 'host') if config.has_option('general', 'host') else DEFAULT_HOST
            Options.port = config.getint('general', 'port') if config.has_option('general', 'port') else DEFAULT_PORT
            Options.workers = config.getint('general', 'workers') if config.has_option('general', 'workers') else DEFAULT_WORKERS
            Options.log_level = config.get('general', 'log_level') if config.has_option('general', 'log_level') else DEFAULT_LOG_LEVEL
            Options.backlog = config.getint('general', 'backlog') if config.has_option('general', 'backlog') else DEFAULT_BACKLOG
            Options.debug = config.getboolean('general', 'debug') if config.has_option('general', 'debug') else DEFAULT_DEBUG
        
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

    if not Options.debug:
        pid = os.fork()
        if pid == 0:
            server.Server(Options).run()
        else:
            sys.exit(0)
    else:
        server.Server(Options).run()
