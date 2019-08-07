#
#  yalab.py
#
import threading
from socket import socket

class EventProcess(threading.Thread):
    def __init__(self, fn, data, on_finish):
        super(EventProcess, self).__init__()
        self.fn = fn
        self.data = data
        self.on_finish = on_finish

    def run(self):
        result = self.fn(self.data)
        if self.on_finish:
            self.on_finish(result)


class Pubsub(object):
    def __init__(self):
        self.__events = {}
        self.__on_finish = None

    def add_listener(self, event, cb):
        T = type(cb).__name__
        if T != 'method' and T != 'function' :
            raise ValueError('PubSub add_listener callback must be a function')
        self.__events.setdefault(event, [])
        self.__events[event].append(cb)

    def emit(self, event, data):
        for listener in self.__events.get(event) or []:
            worker = EventProcess(listener, data, self.__on_finish)
            worker.start()

    def on_finish_result(self, cb):
        T = type(cb).__name__
        if T != 'method' and T != 'function' :
            raise ValueError('PubSub on_finish_result callback must be a method')
        self.__on_finish = cb


# UNSUSED
def prop(x, doc):
    def fget(self):
        return getattr(self, x)

    def fset(self, value):
        setattr(self, x, value)

    def fdel(self):
        delattr(self, x)

    return property(fget, fset, fdel, doc)


class SocketEventGateway(object):
    def __init__(self):
        self._events = Pubsub() 
        self._events.on_finish_result(self._on_reply)

    def on(self, event: str, fn):
        self._events.add_listener(event, fn)

    def emit(self, event, payload):
        self._events.emit(event, payload)

    def process(self, connection: socket, data, addr):
        self._connection = connection
        self._endpoint = addr
        self._received = data
        event, data = self.on_receive(self._received, addr)
        if event:
            self._events.emit(event, data)

    def _on_reply(self, data):
        if data:
            processed_reply = self.on_reply(data, self._endpoint)
            try:
                self._connection.send(processed_reply)
            except OSError:
                self._connection.sendto(processed_reply, self._endpoint)

    # returns tuple (event, data)
    def on_receive(self, data, addr):
        print('WARINIG: no override definition for Gateway.on_receive in child class.')
        return (None, data) 

    # returns structured data
    def on_reply(self, data, addr):
        print('WARNING: no override definition for Gateway.on_reply in child class.')
        return data


