"""
Module management
"""

import sys
import importlib

from logger import Logger
from config import Config
from event import Event

class Module:
    
    # default configuration values
    DEFAULTS = {
        'modules_path': '/usr/lib/motherbee/modules'
    }

    # configuration
    config = {}

    # loaded modules
    # name -> loaded: 1/0
    #      -> object: object
    modules = {}
    
    # already loaded module files
    loaded_files = []

    @staticmethod
    def init():
        Module.loadConfig()
        Module.loadModules()
        Module.startAllModules()
        Event.register('core.reload', Module.reloadEvent)

    @staticmethod
    def loadConfig():
        Module.config['modules_path'] = Config.get('general', 'modules_path', Module.DEFAULTS['modules_path'])
        Module.config['modules'] = Config.get('general', 'modules')
        if not Module.config['modules_path'] in sys.path:
            sys.path.append(Module.config['modules_path'])

    @staticmethod
    def reloadEvent():
        Module.loadConfig()
        Module.loadModules()
        Module.startAllModules()

    @staticmethod
    def register(name, obj):
        if name in Module.modules:
            Logger.warn('module %s already registered', name)
        else:
            if not hasattr(obj, 'init'):
                Logger.warn('Could not register module %. The provided object doesn\'t have an init() method')
            else:
                Module.modules[name] = {
                    'object': obj,
                    'started': False
                }

    @staticmethod
    def loadModules():
        # load external modules
        for m in Module.config['modules'].split(','):
            m = m.strip()
            if len(m) == 0:
                continue
            if m in Module.loaded_files:
                continue
            try:
                Logger.debug('loading module ' + m)
                importlib.import_module(m)
                Module.loaded_files.append(m)
            except Exception as e:
                Logger.error('error while loading module ' + m)
                Logger.exception(str(e))

    @staticmethod
    def startAllModules():
        for m in Module.modules:
            Module.startModule(m)

    @staticmethod
    def startModule(m):
        if Module.modules[m]['started'] == False:
            try:
                Module.modules[m]['object'].init()
                Module.modules[m]['started'] = True
            except Exception as e:
                Logger.error('error while starting module %s', m)
                Logger.exception(str(e))