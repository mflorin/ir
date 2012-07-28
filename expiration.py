"""
Implements expiration of item reservation entries
"""

import os
import signal
import sys
import time
import threading

from logger import Logger
from product import Product
from event import Event

class Expiration(threading.Thread):

    """
    Class constructor
    """
    def __init__(self, options):

        self.running = False

        # application options
        self.options = options

        # event object used for sleeping
        self.event = threading.Event()

        Event.register('reload', self.reloadEvent)

        super(Expiration, self).__init__()

    """
    Cleanup thread
    """
    def run(self):
        
        while self.running:
            now = time.time()
            for sku in Product.productLocks:
                if sku in Product.reserved:
                    Product.lock(sku)
                    _expired = []
                    for clid in Product.reserved[sku]:
                        if now - Product.reserved[sku][clid][1] > self.options.ttl:
                            Logger.info("reservation for product " + sku + " and client " + str(clid) + " expired")
                            _expired.append(clid)
                    for clid in _expired:
                        Product.totalReservations[sku] -= Product.reserved[sku][clid][0]
                        del Product.reserved[sku][clid]
                    del _expired
                    Product.unlock(sku)

            self.event.wait(self.options.cleanup_interval)

    def start(self):
        if not self.running:
            Logger.info('starting the TTL manager')
            self.running = True
            super(Expiration, self).start()

    def stop(self):
        if self.running:
            Logger.info('stopping the TTL manager')
            self.running = False
            self.event.set()
            # in case of a reload, the event flag has to be clear
            # so that the next wait would actually wait
            self.event.clear()
            self.join()

    def reloadEvent(self, *args):
        self.stop()
        # we need this to start the thread again
        super(Expiration, self).__init__()
        self.start()

