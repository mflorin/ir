#!/usr/bin/python

import sys, server, argparse, os

class Options(object):
    pass

if __name__ == "__main__":

    VERB_LOWEST = 1
    VERB_LOW = 2
    VERB_MEDIUM = 3
    VERB_HIGH = 4
    VERB_HIGHEST = 5

    DEFAULT_PORT = 2000
    DEFAULT_WORKERS = 200
    DEFAULT_QUEUE_SIZE = 5
    DEFAULT_VERBOSITY = VERB_MEDIUM
    DEFAULT_BACKLOG = 999999

    VERSION = "1.0.0"

    parser = argparse.ArgumentParser(description='Item Reservation Server', prog='IR')

    parser.add_argument('-f', '--file', type=file, help="configuration file")

    parser.add_argument('--host', 
        default = '',
        help = "address to bind (default 0.0.0.0)")

    parser.add_argument('-p', '--port', 
        type = int,
        default = DEFAULT_PORT,
        help = "port to listen to (default " + str(DEFAULT_PORT) + ")")

    parser.add_argument('-w', '--workers', 
        type=int,
        default = DEFAULT_WORKERS,
        help="maximum number of workers (default " + str(DEFAULT_WORKERS) + ")")

    parser.add_argument('-b', '--backlog', 
        type=int,
        default = DEFAULT_BACKLOG,
        help="TCP backlog (default " + str(DEFAULT_BACKLOG) + ")")

    parser.add_argument('-q', '--queue_size', 
        type = int,
        default = DEFAULT_QUEUE_SIZE,
        help = "worker's queue size (default " + str(DEFAULT_QUEUE_SIZE) + ")")
    parser.add_argument('-v', '--verbosity',
        type = int,
        default = DEFAULT_VERBOSITY,
        help="verbosity level " + str(DEFAULT_VERBOSITY)+ " - lowest, " \
                + str(VERB_HIGHEST) + " - highest")
    parser.add_argument('-d', '--debug', 
        action='store_true',
        default = False,
        help="don't detach (runs a single thread) for debugging purposes")

    parser.add_argument('--version', 
        action='version', 
        version='%(prog)s ' + str(VERSION))

    parser.parse_args(sys.argv[1:], namespace = Options)

    if not Options.debug:
        pid = os.fork()
        if pid == 0:
            server.Server(Options).run()
        else:
            sys.exit(0)
    else:
        server.Server(Options).run()
