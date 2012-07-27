"""
Implements expiration of item reservation entries
"""

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
        super(Expiration, self).__init__()

    """
    Cleanup thread
    """
    def run(self):
        
        while self.running:
            Logger.marker()
            now = time.time()
            for sku,r in Product.reservations():
                for clid in r:
                    if now - r[clid][1] > self.ttl:
                        Logger.info("reservation for product " + sku + " and client " + str(clid) + " expired")
                        del r[clid]

            time.sleep(self.interval)
    
    def stop(self):
        self.running = False
