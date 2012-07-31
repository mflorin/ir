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
from options import Options

class Expiration(threading.Thread):

    """
    Module startup
    """
    def __init__(self, options):

        self.running = False

        # application options
        self.options = {}

        self.options['ttl'] = Options.getint('expiration', 'ttl')
        self.options['cleanup_interval'] = Options.getint('expiration', 'cleanup_interval')

        # event object used for sleeping
        self.event = threading.Event()

        Event.register('reload', self.reloadEvent)
        Event.register('shutdown', self.shutdownEvent)

        super(Expiration, self).__init__()

    """
    Cleanup thread
    """
    def run(self):
        
        while self.running:
            now = time.time()
            for [sku, _pdata] in Product.getProducts():

                _expired = []
                for [clid, _rdata] in Product.getReservations(sku):
                    if now - Product.reservationGetTimeUnlocked(sku, clid) > self.options.ttl:
                        Logger.info("reservation for product " + sku + " and client " + str(clid) + " expired")
                        _expired.append(clid)
                for clid in _expired:
                    Product.totalReservationsDecUnlocked(sku, Product.reservationGetQtyUnlocked(sku, clid))
                    Product.reservationDelUnlocked(sku, clid)
                del _expired
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

    def shutdownEvent(self, *args):
        self.stop()



# initialize the expiration module
expiration = Expiration(Options.expiration)
expiration.start()
