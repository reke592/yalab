#
# yalab.py
#
# TODO: change Pubsub emit, include the callback in queue instead of using a bottle-neck callback ._on_finish_result
#
from socket import socket
import threading
import queue
import time
import re

# params:
#   idle : int, time offset in seconds before thread go to sleep(1), when queue is empty
#   worker_ct : int, number of daemon thread workers in thread pool
class Pubsub(object):
    def __init__(self, worker_ct=1, idle=1):
        self.__events = {}
        self.__on_finish = None
        self.q = queue.Queue()
        self.lock = threading.Lock()
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
            listener_fn, args, cb = self.q.get()
            result = listener_fn(args)
            if cb:
                print(result)
                cb(result)
            self.q.task_done()

    def add_listener(self, event, cb):
        T = type(cb).__name__
        if T != 'method' and T != 'function' :
            raise ValueError('PubSub add_listener callback must be a function')
        self.__events.setdefault(event, [])
        self.__events[event].append(cb)

    def listeners(self, event):
        return self.__events.get(event) or []

    def emit(self, event, data, cb=None):
        for listener in self.__events.get(event) or []:
            self.q.put((listener, data, cb))
        self.idle_mode.clear()

    def on_finish_result(self, cb):
        T = type(cb).__name__
        if T != 'method' and T != 'function' :
            raise ValueError('PubSub on_finish_result callback must be a method')
        self.__on_finish = cb


class SocketEventGateway(object):
    def __init__(self, worker_ct=1):
        print('Gateway thread pool: %d' % worker_ct)
        self.tcp_port = None
        self.udp_port = None
        self.dsdp_interval = None
        self.multicast_addr = None
        self._events = Pubsub(worker_ct) 
        self._events.add_listener('__RECEIVED__', self.on_receive)
        self._events.add_listener('__RESPONSE__', self.on_reply)
        self._events.add_listener('__SEND_REPLY__', self.on_send)
        #self._events.on_finish_result(self._on_reply)

    def on(self, event: str, fn):
        self._events.add_listener(event, fn)

    def emit(self, event, payload, cb=None):
        self._events.emit(event, payload, cb)

    def process(self, connection: socket, data, addr):
        self._connection = connection
        self._endpoint = addr
        self._received = data
        self.emit('__RECEIVED__', (data, addr))
        #event, data = self.on_receive(self._received, addr)
        #if event:
        #    self._events.emit(event, data, self._on_reply)

    def remove_listener(self, event, listener):
        try:
            self._events.listeners(event).remove(listener)
        except:
            pass 

    def configure(self, **kwargs):
        tcp = kwargs.get('tcp')
        udp = kwargs.get('udp')
        mgrp = kwargs.get('multicast_group')
        dsdp_i = kwargs.get('dsdp_interval')
        if type(tcp) is int:
            self.tcp_port = tcp
        if type(udp) is int:
            self.udp_port = udp
            if re.match(r'(?:\d{1,3}\.){3}(\d{1,3})$', mgrp):
                self.multicast_addr = (mgrp, udp)
        if type(dsdp_i) is int or type(dsdp_i) is float:
            self.dsdp_interval = dsdp_i

    def on_send(self, response):
        if response:
            data, addr = response
            try:
                self._connection.send(data)
            except OSError:
                self._connection.sendto(data, addr)

    # wait all queued process to finish
    def join(self):
        self._events.q.join()

    # returns tuple (event, data)
    def on_receive(self, received):
        print('WARINIG: no override definition for Gateway.on_receive in child class.')
        return None 

    # returns structured data
    def on_reply(self, response):
        print('WARNING: no override definition for Gateway.on_reply in child class.')
        self.emit('__SEND_REPLY__', None) 

