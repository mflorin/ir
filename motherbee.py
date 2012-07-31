#!/usr/bin/python

import os
import sys
import signal
import socket
import logging
import argparse

import config
from server import Server
from logger import Logger
from module import Module

VERSION = "2.0.0"

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog=config.Config.APP_NAME
    )

    parser.add_argument('-f', '--file', 
        default=config.Config.general.file, 
        help="configuration file")

    parser.add_argument('-d', '--debug',
        default = config.Config.general.debug,
        action='store_true',
        help="run in console, don't detach")

    parser.add_argument('--version', 
        action='version', 
        version='%(prog)s ' + str(VERSION))

    try:
        parser.parse_args(sys.argv[1:], namespace = config.Config.general)
    except:
        sys.exit(1)

    
    config.Config.init()
    Logger.init()
    Module.init()

    if config.Config.general.debug:       
        # run the server attached to the console
        Server().run()
    else:
        # run the server in background
        pid = os.fork()
        if pid == 0:
            Server().run()
        else:
            sys.exit(0)
