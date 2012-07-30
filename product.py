import time
import threading

from logger import Logger
from command import Command
from event import Event

class Product:
     
    # product data
    # sku1
    #   -> totalReservations
    #   -> reservations
    #       -> clid1
    #           -> qty: quantity 
    #           -> timestamp: timestamp when the reservation was updated
    #       -> clid2 ...
    #   -> stock
    #   -> lock
    # sku2 ...
    data = {}

    # big lock used around all products when saving or loading the database
    # this does not actually impact commands altering the product, it only
    # affects adding new products or saving and loading the db in the same time
    bigLock = threading.RLock()
    
    @staticmethod
    def init():

        commands = {
            'product.add': {'handler': Product.productAddCmd, 'args':2, 'help':'productAdd sku stock'},
            'product.info': {'handler': Product.productInfoCmd, 'args':1, 'help':'productInfo sku'},
            'reservation.add': {'handler': Product.reservationAddCmd, 'args':3, 'help':'reservationAdd client_id sku qty'},
            'reservation.del': {'handler': Product.reservationDelCmd, 'args':3, 'help':'reservationDel client_id sku qty'},
            'reservation.set': {'handler': Product.reservationSetCmd, 'args':3, 'help':'reservationSet client_id sku qty'},
            'stock.set': {'handler': Product.stockSetCmd, 'args':2, 'help':'stockSet sku stock'},
            'stock.dec': {'handler': Product.stockDecCmd, 'args':2, 'help':'stockDec sku qty'},
            'stock.get': {'handler': Product.stockGetCmd, 'args':1, 'help':'stockGet sku'},
            'product.total': {'handler': Product.totalCmd, 'args':0, 'help':'status'}
        }


        for c in commands:
            Command.register(
                commands[c]['handler'], 
                c, 
                commands[c]['args'], 
                commands[c]['help']
            )

        Event.register('db.save', Product.saveDb)
        Event.register('db.load', Product.loadDb)

    """
    Prepare data to be written in the database
    """
    @staticmethod
    def saveDb(data):
        dbdata = {}
        Product.lockAll()
        for sku in Product.data:
            Product.lock(sku)
            dbdata[sku] = {
                'totalReservations': Product.data[sku]['totalReservations'],
                'reservations': dict(Product.data[sku]['reservations']),
                'stock': Product.data[sku]['stock']
            }
            Product.unlock(sku)
        Product.unlockAll()
        data['products'] = dbdata
        return True

    """
    Interpret loaded db data and fill in product data
    """
    @staticmethod
    def loadDb(data):
        
        Product.lockAll()

        if not 'products' in data:
            return False
        
        products = data['products']
        for sku in products:
            if Product.lock(sku) == False:
                # adding a new product
                Product.productAdd(sku, products[sku]['stock'])
                Product.lock(sku)
           
            Product.data[sku]['reservations'] = dict(products[sku]['reservations'])
            Product.data[sku]['totalReservations'] = products[sku]['totalReservations']
            Product.data[sku]['stock'] = products[sku]['stock']
            
            Product.unlock(sku)

        Product.unlockAll()

    @staticmethod
    def lock(sku):
        if not sku in Product.data:
            return False
        Product.data[sku]['lock'].acquire()
        return True

    @staticmethod
    def unlock(sku):
        if not sku in Product.data:
            return False
        Product.data[sku]['lock'].release()
        return True

    @staticmethod
    def lockAll():
        Product.bigLock.acquire()

    @staticmethod
    def unlockAll():
        Product.bigLock.release()

    @staticmethod
    def getProducts():
        Product.lockAll()
        for sku in Product.data:
            Product.lock(sku)
            yield [sku, Product.data[sku]]
            Product.unlock(sku)
        Product.unlockAll()

    @staticmethod
    def getReservations(sku):
        Product.lock(sku)
        for clid in Product.data[sku]['reservations']:
            yield [clid, Product.data[sku][clid]]
        Product.unlock(sku)

    @staticmethod
    def reservationGetTimeUnlocked(sku, clid):
        return Product.data[sku]['reservations'][clid]['timestamp']

    @staticmethod
    def reservationGetQtyUnlocked(sku, clid):
        return Product.data[sku]['reservations'][clid]['qty']

    @staticmethod
    def reservationDelUnlocked(sku, clid):
        del Product.data[sku]['reservations'][clid]

    @staticmethod
    def totalReservationsDecUnlocked(sku, qty):
        Product.data[sku]['totalReservations'] -= qty

    @staticmethod
    def totalReservationsIncUnlocked(sku, qty):
        Product.data[sku]['totalReservations'] += qty


    """ ---------------------- COMMANDS ---------------------- """

    """
    productAdd command
    """
    @staticmethod
    def productAddCmd(args):

        sku = args[0]
        stock = int(args[1])

        if Product.productAdd(sku, stock):
            Logger.debug("product %s with stock %d was added" % (sku, stock))
            return Command.result(Command.RET_SUCCESS)
        else:
            return Command.result(Command.RET_ERR_GENERAL)


    """
    set the stock
    """
    @staticmethod
    def stockSetCmd(args):
        
        sku = args[0]
        qty = int(args[1])

        if Product.stockSet(sku, qty):
            return Command.result(Command.RET_SUCCESS)
        else:
            return Command.result(Command.RET_ERR_GENERAL)

    """
    get the stock
    """
    @staticmethod
    def stockGetCmd(args):

        stock = Product.stockGet(args[0])
        if not stock:
            return Command.result(Command.RET_ERR_GENERAL, 'product not found')
        else:
            return Command.result(Command.RET_SUCCESS, stock)

    """
    decrease the stock
    """
    @staticmethod
    def stockDecCmd(args):

        sku = args[0]
        qty = int(args[1])

        ret = Product.stockDec(sku, qty)
        if ret > -1:
            return Command.result(Command.RET_SUCCESS, {'stock': ret})
        else:
            return Command.result(Command.RET_ERR_GENERAL)

    """
    reservationAdd command
    """
    @staticmethod
    def reservationAddCmd(args):

        clid = args[0]
        sku = args[1]
        qty = int(args[2])

        ret = Product.reservationAdd(sku, clid, qty)
        if ret > -1:
            return Command.result(Command.RET_ERR_GENERAL, 'not enough stock (stock: ' + str(ret) + ')')
        else:
            return Command.result(Command.RET_SUCCESS)

    """
    reservationDel command
    """
    @staticmethod
    def reservationDelCmd(args):
       clid = args[0]
       sku = args[1]
       qty = int(args[2])
       Product.reservationDel(sku, clid, qty)
       return Command.result(Command.RET_SUCCESS)

    """
    reservationSet command
    """
    @staticmethod
    def reservationSetCmd(args):
       clid = args[0]
       sku = args[1]
       qty = int(args[2])
       Product.reservationSet(sku, clid, qty)
       ret = Product.reservationSet(sku, clid, qty)
       if ret > 0:
           return Command.result(Command.RET_ERR_GENERAL, 'not enough stock (stock: ' + str(ret) + ')')
       else:
           return Command.result(Command.RET_SUCCESS)

    """
    get info on a product
    """
    @staticmethod
    def productInfoCmd(args):
        ret = Product.info(args[0])
        if not ret:
            return Command.result(Command.RET_ERR_GENERAL, 'product not found')
        else:
            return Command.result(Command.RET_SUCCESS, ret)

    """
    get system status
    """
    @staticmethod
    def totalCmd(args):
        ret = {
            'products': len(Product.data),
        }
        return Command.result(Command.RET_SUCCESS, ret)




    """
    Add a product to the library.
    We create a lock for it 
    """
    @staticmethod
    def productAdd(sku, stock):
        Product.lockAll()
        if not sku in Product.data:
            Product.data[sku] = {
                'reservations': {},
                'totalReservations': 0,
                'stock': stock,
                'lock': threading.RLock()
            }
        else:
            Logger.warn('product %s already exists' % sku)
        Product.unlockAll()
        return True

    """
    Set the stock
    """
    @staticmethod
    def stockSet(sku, stock):
        # direct list assignement is atomic
        Product.data[sku]['stock'] = stock
        return True
    
    """
    Decrement from stock
    """
    @staticmethod
    def stockDec(sku, stock):

        ret = 0

        if not Product.lock(sku):
            return -1

        # -= is non atomic, needs locking
        Product.data[sku]['stock'] -= stock
        if Product.data[sku]['stock'] < 0:
            Product.data[sku]['stock'] = 0
        ret = Product.data[sku]['stock']

        Product.unlock(sku)

        return ret

    """
    Retreive stock
    """
    @staticmethod
    def stockGet(sku):
        return Product.data[sku]['stock'] if sku in Product.data else None


    """
    Reserve a qty for a client

    @return -1 on success (yeah, I know, weird)
    @return current stock if we don't have enough items in stock
    """
    @staticmethod
    def reservationAdd(sku, clid, qty):
        
        ret = -1

        if Product.lock(sku) == False:
            return 0
        
        stock = Product.stockGet(sku)

        if Product.data[sku]['totalReservations'] + qty <= stock:
            Product.data[sku]['reservations'][clid]['qty'] += qty
            Product.data[sku]['reservations'][clid]['timestamp'] = time.time()
            Product.data[sku]['totalReservations'] += qty
        else:
            ret = stock

        Product.unlock(sku)
        
        return ret

    """
    Remove items from a reservation
    """
    @staticmethod
    def reservationDel(sku, clid, qty):
        
        if Product.lock(sku) == False:
            return False
       

        Product.data[sku]['totalReservations'] -= qty
        if Product.data[sku]['totalReservations'] < 0 :
            Product.data[sku]['totalReservations'] = 0
        Product.data[sku]['reservations'][clid]['qty'] -= qty
        Product.data[sku]['reservations'][clid]['timestamp'] = time.time()
        if Product.data[sku]['reservations'][clid]['qty'] < 0:
            Product.data[sku]['reservations'][clid]['qty'] = 0

        Product.unlock(sku)

        return True

    """
    Set the number of reserved items
    """
    @staticmethod
    def reservationSet(sku, clid, qty):
        
        ret = 0

        Product.lock(sku)
       
        Product._initProductUnlocked(sku, clid)

        stock = Product.stockGet(sku)

        diff = qty - Product.data[sku]['reservations'][clid]['qty']
        if Product.data[sku]['totalReservations'] + diff <= stock:
            Product.data[sku]['reservations'][clid]['qty'] = qty
            Product.data[sku]['reservations'][clid]['timestamp'] = time.time()
            Product.data[sku]['totalReservations'] += diff
        else:
            ret = stock


        Product.unlock(sku)

        return ret


    """
    Get info on a product
    """
    @staticmethod
    def info(sku):
        if not sku in Product.data:
            return None
        # TODO: should we really lock?
        return {
            'stock': Product.stockGet(sku),
            'reservations': Product.data[sku]['totalReservations'] if sku in Product.data else 0
        }



# initialize the product module
Product.init()


