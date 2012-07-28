#!/usr/bin/python

import os
import sys
import signal
import socket
import logging
import argparse

from options import Options
from server import Server
from logger import Logger
from db import Db

def hand(sig, f):
    print "test"
 
signal.signal(signal.SIGUSR1, hand)

VERSION = "1.0.0"

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description='Item Reservation Server', 
        prog='ItemReservation'
    )

    parser.add_argument('-f', '--file', 
        default=Options.general.file, 
        help="configuration file")

    parser.add_argument('-d', '--debug',
        default = Options.general.debug,
        action='store_true',
        help="run in console, don't detach")

    parser.add_argument('--version', 
        action='version', 
        version='%(prog)s ' + str(VERSION))

    try:
        parser.parse_args(sys.argv[1:], namespace = Options.general)
    except:
        sys.exit(1)

    
    Options.init()
    Options.load()

    Logger.init(Options.logger)

    if Options.general.debug:
        # add console logging
        ch = logging.StreamHandler()
        ch.setLevel(Options.logger.log_level)
        ch.setFormatter(Logger.getFormatter())
        Logger.logger.addHandler(ch)
        
        # run the server attached to the console
        Server(Options).run()
    else:
        # run the server in background
        pid = os.fork()
        if pid == 0:
            Server(Options).run()
        else:
            sys.exit(0)
