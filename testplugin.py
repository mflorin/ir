"""
This is a test plugin
"""

from event import Event
from command import Command
from logger import Logger

class TestPlugin:
    
    @staticmethod
    def init():
        Event.register('reload', TestPlugin.reloadEvent)
        Command.register(TestPlugin.helloCmd, 'hello', 0, 'hello')

    @staticmethod
    def reloadEvent(args):
        Logger.info('TestPlugin reload handler called')

    @staticmethod
    def helloCmd(*args):
        Logger.info('Hello from TestPlugin')
        return Command.result(Command.RET_SUCCESS)


TestPlugin.init()
