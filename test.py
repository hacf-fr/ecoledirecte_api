from functools import wraps


# Create a class to house the methods
class fires(object):
    @staticmethod
    def whenCalled(event):
        e = (lambda s: getattr(s, event)) if type(event) == str else (lambda s: event)

        def decorator(f):
            """Fires the event before the function executes"""

            @wraps(f)
            def wrapped(self, *args, **kargs):
                e(self).fire(*args, **kargs)
                return f(self, *args, **kargs)

            return wrapped

        return decorator

    @staticmethod
    def onceComplete(event):
        e = (lambda s: getattr(s, event)) if type(event) == str else (lambda s: event)

        def decorator(f):
            """Fires the event after the function executes"""

            @wraps(f)
            def wrapped(self, *args, **kargs):
                result = f(self, *args, **kargs)
                e(self).fire(*args, **kargs)
                return result

            return wrapped

        return decorator

    __call__ = whenCalled


# but then create one instance and hide the class from outside
fires = fires()


class Event:
    def __init__(self):
        self.handlers = set()

    def handle(self, handler):
        self.handlers.add(handler)
        return self

    def unhandle(self, handler):
        try:
            self.handlers.remove(handler)
        except:
            raise ValueError(
                "Handler is not handling this event, so cannot unhandle it."
            )
        return self

    def fire(self, *args, **kargs):
        for handler in self.handlers:
            handler(*args, **kargs)

    @property
    def handlerCount(self):
        return len(self.handlers)

    __iadd__ = handle
    __isub__ = unhandle
    __call__ = fire
    __len__ = handlerCount


class test(object):
    def __init__(self):
        self.onTested = Event()

    @fires.onceComplete("onTested")
    def foo(self, x):
        print("Called foo with", x)

    @fires.whenCalled("onTested")
    def bar(self, y):
        print("Called bar with", y)


t = test()


def handler(x):
    print("Test with", x)


t.onTested += handler

t.foo(2)
t.bar(3)
