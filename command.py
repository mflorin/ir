import json
from product import Product
from logger import Logger

class Command:

    commands = {
        'productAdd': [2, 'productAdd sku stock'],
        'reservationAdd': [3, 'reservationAdd client_id sku qty'],
        'reservationDel': [3, 'reservationDel client_id sku qty'],
        'reservationSet': [3, 'reservationSet client_id sku qty'],
        'stockSet': [2, 'stockSet sku stock'],
        'stockDec': [2, 'stockDec sku qty'],
        'stockGet': [1, 'stockGet sku'],
        'info': [1, 'info sku']
    }

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
            return Command.result(Command.RET_ERR_CMD)
        
        # check the number of parameters
        cmdInfo = Command.commands[cmd]
        if len(args[1:]) != cmdInfo[0]:
            Logger.error(cmd + " needs " + str(cmdInfo[0]) + " arguments. Only " + str(len(args[1:])) + " were given. Received command was `" + str(args) + "`")
            return Command.result(Command.RET_ERR_ARGS, cmdInfo[1])
         
        return f(args[1:])
            
    """
    packs the result and returns it
    """
    @staticmethod
    def result(code = 0, msg = None):

        if not Command.returnCodes[code]:
            ret = {
                'code': -1,
                'data': 'internal error'
            }
        else:
            ret = {'code': code}
            if not msg:
                ret['data'] = Command.returnCodes[code]
            else:
                ret['data'] = msg

        return json.dumps(ret)
       

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
        if ret > 0:
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
    def infoCmd(args):
        ret = Product.info(args[0])
        if not ret:
            return Command.result(Command.RET_ERR_GENERAL, 'product not found')
        else:
            return Command.result(Command.RET_SUCCESS, ret)

