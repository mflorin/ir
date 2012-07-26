
class Command:

    returnCodes = {
        0: 'success',
        1: 'no such command'
    }

    """ 
    process a command and return a string
    as a result
    """
    @classmethod 
    def processCmd(cls, args):
        cmd = args[0]
        f = getattr(Command, cmd, None)
        if cmd in ['processCmd', 'result'] or not f or not callable(f):
            return Command.result(1, [cmd])
        
        return f(args[1:])
            
    """
    packs the result and returns it
    """
    @classmethod
    def result(cls, code = 0, data = None):
        if not Command.returnCodes[code]:
            return 'res: -1, msg: internal error, data: ' + str(code)
        ret = 'res: ' + str(code) + ', msg: ' + Command.returnCodes[code]
        if data:
            ret += ', data: ' + ','.join(data)
        return ret
        
