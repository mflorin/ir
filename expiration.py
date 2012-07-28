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

class Expiration(threading.Thread):

    """
    Class constructor
    @param interval Interval to clean up expired entries
    """
    def __init__(self, interval, ttl):
        self.interval = interval
        self.ttl = ttl
        self.running = True

        # event object used for sleeping
        self.event = threading.Event()

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
                        if now - Product.reserved[sku][clid][1] > self.ttl:
                            Logger.info("reservation for product " + sku + " and client " + str(clid) + " expired")
                            _expired.append(clid)
                    for clid in _expired:
                        Product.totalReservations[sku] -= Product.reserved[sku][clid][0]
                        del Product.reserved[sku][clid]
                    del _expired
                    Product.unlock(sku)

            self.event.wait(self.interval)
    
    def stop(self):
        self.running = False
        self.event.set()
