"""
Event management engine
"""

class Event:
    
    observers = {}

    """
    Register an observer for an event
    """
    @staticmethod
    def register(event, observer):
        if not event in Event.observers:
            Event.observers[event] = []
        Event.observers[event].append(observer)

    """
    Dispatch an event to all its observers
    """
    @staticmethod
    def dispatch(event, *args):
        if event in Event.observers:
            for obs in Event.observers[event]:
                obs(args)
        return True
        
