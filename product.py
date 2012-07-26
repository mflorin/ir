import threading

class Product:
    
    # reserved quantities dictionary
    # sku1 ->
    #   clid1 -> qty1
    #   clid2 -> qty2
    #   ...
    # sku2 -> 
    # ...
    # skun ->
    reserved = {}

    # product stock dictionary
    # sku -> stock
    stock = {}

    # total number of reservations for each sku
    # used to avoid walking the reserved dict to 
    # find out the total number of reservations
    totalReservations = {}

    # we're using per product locks
    # to avoid locking an entire list of
    # products and allow operating on 
    # two or more products in the same time
    productLocks = {}

    @staticmethod
    def lock(sku):
        if not sku in Product.productLocks:
            print "NO LOCK FOR " + sku
            return False
        Product.productLocks[sku].acquire()
        return True

    @staticmethod
    def unlock(sku):
        if not sku in Product.productLocks:
            print "NO LOCK FOR " + sku
            return False
        Product.productLocks[sku].release()
        return True

    @staticmethod
    def _initProductUnlocked(sku, clid):
        if not sku in Product.totalReservations:
            Product.totalReservations[sku] = 0

        if not sku in Product.reserved:
            Product.reserved[sku] = {}

        if not clid in Product.reserved[sku]:
            Product.reserved[sku][clid] = 0


    """
    Add a product to the library.
    We create a lock for it 
    """
    @staticmethod
    def productAdd(sku, stock):
        Product.productLocks[sku] = threading.RLock()
        Product.stock[sku] = stock
        return True


    """
    Set the stock
    """
    @staticmethod
    def stockSet(sku, stock):
        # direct list assignement is atomic
        Product.stock[sku] = stock
    
    """
    Decrement from stock
    """
    @staticmethod
    def stockDec(sku, stock):

        ret = 0

        Product.lock(sku)

        if sku not in Product.stock:
            Product.stock[sku] = 0
        
        else:
            # -= is non atomic, needs locking
            Product.stock[sku] -= stock
            if Product.stock[sku] < 0:
                Product.stock[sku] = 0
            ret = Product.stock[sku]

        Product.unlock(sku)

        return ret

    """
    Retreive stock
    """
    @staticmethod
    def stockGet(sku):
        return Product.stock[sku] if sku in Product.stock else 0


    """
    Reserve a qty for a client

    @return 0 on success
    @return current stock if we don't have enough items in stock
    """
    @staticmethod
    def reservationAdd(sku, clid, qty):
        
        ret = 0

        Product.lock(sku)
        
        Product._initProductUnlocked(sku, clid)

        stock = Product.stockGet(sku)

        if Product.totalReservations[sku] + qty <= stock:
            Product.reserved[sku][clid] += qty
            Product.totalReservations[sku] += qty
        else:
            ret = stock

        Product.unlock(sku)
        
        return ret

    """
    Remove items from a reservation
    """
    @staticmethod
    def reservationDel(sku, clid, qty):
        
        Product.lock(sku)
       
        Product._initProductUnlocked(sku, clid)

        Product.totalReservations[sku] -= qty
        if Product.totalReservations[sku] < 0 :
            Product.totalReservations[sku] = 0
        Product.reserved[sku][clid] -= qty
        if Product.reserved[sku][clid] < 0:
            Product.reserved[sku][clid] = 0

        Product.unlock(sku)

        return True

    """
    Get info on a product
    """
    @staticmethod
    def info(sku):
        # TODO: should we really lock?
        return {
            'stock': Product.stockGet(sku),
            'reserved': Product.totalReservations[sku] if sku in Product.totalReservations else 0
        }
