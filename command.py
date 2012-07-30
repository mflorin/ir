import json
from logger import Logger

class Command:

    # character ending a command
    SEPARATOR = "\n"

    commands = {}

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
    register a command
    @param handler Command handler
    @param cmd Command
    @param nargs Number of arguments the command receives
    @param help Help string
    """
    @staticmethod
    def register(handler, cmd, args, help = None):
        if cmd in Command.commands:
            return False
        Command.commands[cmd] = {
            'args': args, 
            'help': help, 
            'handler': handler
        }
        return True

    """ 
    process a command and return a string
    as a result
    """
    @staticmethod 
    def processCmd(args):
        cmd = args[0]
        if cmd not in Command.commands:
            return Command.result(Command.RET_ERR_CMD)

        if 'handler' in Command.commands[cmd]:
            f = Command.commands[cmd]['handler']

        if not f or not callable(f):
            return Command.result(Command.RET_ERR_CMD)

        # check the number of parameters
        cmdInfo = Command.commands[cmd]
        if len(args[1:]) != cmdInfo['args']:
            Logger.error(cmd + " needs " + str(cmdInfo['args']) + " arguments. Only " + str(len(args[1:])) + " were given. Received command was `" + str(args) + "`")
            return Command.result(Command.RET_ERR_ARGS, cmdInfo['help'])
        try: 
            return f(args[1:])
        except Exception as e:
            Logger.critical(str(e))
            return Command.result(Command.RET_ERR_GENERAL, str(e))
            
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
       

