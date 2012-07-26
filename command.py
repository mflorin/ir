from product import Product

class Command:

    commands = [ 
        'productAdd',
        'reservationAdd', 
        'reservationDel',
        'reservationSet',
        'stockSet',
        'stockDec',
        'stockGet',
        'info'
    ]

    returnCodes = {
        0: 'success',
        100: 'no such command',
        200: 'invalid number of arguments',
        300: 'error'
    }

    RET_SUCCESS = 0
    RET_ERR_CMD = 100
    RET_ERR_ARGS = 200
    RET_ERR_GENERAL = 300

    """ 
    process a command and return a string
    as a result
    """
    @staticmethod 
    def processCmd(args):
        cmd = args[0]
        f = getattr(Command, cmd + 'Cmd', None)
        if cmd not in Command.commands or not f or not callable(f):
            return Command.result(Command.RET_ERR_CMD, [cmd])
        
        return f(args[1:])
            
    """
    packs the result and returns it
    """
    @staticmethod
    def result(code = 0, data = None):
        if not Command.returnCodes[code]:
            return 'res: -1, msg: internal error, data: ' + str(code)
        ret = 'res: ' + str(code) + ', msg: ' + Command.returnCodes[code]
        if data:
            ret += ', data: ' + ','.join(data)
        return ret
       

    """ ---------------------- COMMANDS ---------------------- """

    """
    productAdd command
    """
    @staticmethod
    def productAddCmd(args):
        if len(args) != 2:
            return Command.result(Command.RET_ERR_ARGS, ['addProductCmd sku stock'])
        sku = args[0]
        stock = int(args[1])

        if Product.productAdd(sku, stock):
            return Command.result(Command.RET_SUCCESS)
        else:
            return Command.result(Command.RET_ERR_GENERAL)


    """
    set the stock
    """
    @staticmethod
    def stockSetCmd(args):
        if len(args) != 2:
            return Command.result(Command.RET_ERR_ARGS, ['stockSet sku stock'])
        
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
        if len(args) != 1:
            return Command.result(Command.RET_ERR_ARGS, ['stockGet sku'])

        if Product.stockGet(args[0]):
            return Command.result(Command.RET_SUCCESS)
        else:
            return Command.result(Command.RET_ERR_GENERAL)

    """
    decrease the stock
    """
    @staticmethod
    def stockDecCmd(args):
        if len(args) != 2:
            return Command.result(Command.RET_ERR_ARGS, ['stockDec sku qty'])

        sku = args[0]
        qty = int(args[1])

        ret = Product.stockDec(sku, qty)
        if ret > -1:
            return Command.result(Command.RET_SUCCESS, ['stock: ' + str(ret)])
        else:
            return Command.result(Command.RET_ERR_GENERAL)

    """
    reservationAdd command
    """
    @staticmethod
    def reservationAddCmd(args):
        if len(args) != 3:
            return Command.result(Command.RET_ERR_ARGS, ['reservationAdd client_id sku qty'])

        clid = args[0]
        sku = args[1]
        qty = int(args[2])

        ret = Product.reservationAdd(sku, clid, qty)
        if ret > 0:
            return Command.result(Command.RET_ERR_GENERAL, ['not enough stock (' + str(ret) + ')'])
        else:
            return Command.result(Command.RET_SUCCESS)

    """
    reservationDel command
    """
    @staticmethod
    def reservationDelCmd(args):
       if len(args) != 3:
           return Command.result(Command.RET_ERR_ARGS, ['reservationDel client_id sku qty'])
       clid = args[0]
       sku = args[1]
       qty = int(args[2])
       Product.reservationDel(sku, clid, qty)
       return Command.result(Command.RET_SUCCESS)

    """
    get info on a product
    """
    @staticmethod
    def infoCmd(args):
        if len(args) != 1:
            return Command.result(Command.RET_ERR_ARGS, ['info sku'])
        
        ret = Product.info(args[0])
        return Command.result(Command.RET_SUCCESS, [str(ret['reserved']) + '|' + str(ret['stock'])])

