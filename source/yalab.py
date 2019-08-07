#
#  yalab.py
#
from socket import socket
import threading
import queue
import time

#class EventProcess(threading.Thread):
#    def __init__(self, fn, data, on_finish):
#        super(EventProcess, self).__init__()
#        self.fn = fn
#        self.data = data
#        self.on_finish = on_finish
#
#    def run(self):
#        result = self.fn(self.data)
#        if self.on_finish:
#            self.on_finish(result)


#class Pubsub(object):
#    def __init__(self):
#        self.__events = {}
#        self.__on_finish = None
#
#    def add_listener(self, event, cb):
#        T = type(cb).__name__
#        if T != 'method' and T != 'function' :
#            raise ValueError('PubSub add_listener callback must be a function')
#        self.__events.setdefault(event, [])
#        self.__events[event].append(cb)
#
#    def emit(self, event, data):
#        for listener in self.__events.get(event) or []:
#            worker = EventProcess(listener, data, self.__on_finish)
#            worker.start()
#
#    def on_finish_result(self, cb):
#        T = type(cb).__name__
#        if T != 'method' and T != 'function' :
#            raise ValueError('PubSub on_finish_result callback must be a method')
#        self.__on_finish = cb


# params:
#   idle : int, time offset in seconds before thread go to sleep(1), when queue is empty
#   worker_ct : int, number of daemon thread workers in thread pool
class Pubsub(object):
    def __init__(self, worker_ct=1, idle=1):
        self.__events = {}
        self.__on_finish = None
        self.q = queue.Queue()
        self.pool = []
        self.idle_mode = threading.Event()
        self.idle_mode.set()
        self.idle = idle
        for i in range(worker_ct):
            worker = threading.Thread(target=self._process_q, daemon=True)
            self.pool.append(worker)
            worker.start()

    def _sleep(self):
        # wait for next event
        start = time.time()
        while True:
            elapsed = time.time() - start
            if elapsed > self.idle and self.q.empty():
                time.sleep(1)
            else:
                break

    def _process_q(self):
        while True:
            if self.q.empty():
                self._sleep()
            # else
            fn, args = self.q.get()
            result = fn(args)
            if self.__on_finish:
                self.__on_finish(result)
            self.q.task_done()

    def add_listener(self, event, cb):
        T = type(cb).__name__
        if T != 'method' and T != 'function' :
            raise ValueError('PubSub add_listener callback must be a function')
        self.__events.setdefault(event, [])
        self.__events[event].append(cb)

    def emit(self, event, data):
        for listener in self.__events.get(event) or []:
            self.q.put((listener, data))
        self.idle_mode.clear()

    def on_finish_result(self, cb):
        T = type(cb).__name__
        if T != 'method' and T != 'function' :
            raise ValueError('PubSub on_finish_result callback must be a method')
        self.__on_finish = cb


# UNSUSED
#def prop(x, doc):
#    def fget(self):
#        return getattr(self, x)
#
#    def fset(self, value):
#        setattr(self, x, value)
#
#    def fdel(self):
#        delattr(self, x)
#
#    return property(fget, fset, fdel, doc)


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

    # wait all queued process to finish
    def join(self):
        self._events.q.join()

    # returns tuple (event, data)
    def on_receive(self, data, addr):
        print('WARINIG: no override definition for Gateway.on_receive in child class.')
        return (None, data) 

    # returns structured data
    def on_reply(self, data, addr):
        print('WARNING: no override definition for Gateway.on_reply in child class.')
        return data

