#
# test.py
#
import queue
import time
import random
import threading

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
            result = fn(*args)
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
            self.q.put((listener, (event, data)))
        self.idle_mode.clear()

    def on_finish_result(self, cb):
        T = type(cb).__name__
        if T != 'method' and T != 'function' :
            raise ValueError('PubSub on_finish_result callback must be a method')
        self.__on_finish = cb


def test(event, data):
    t = random.random() * 3
    time.sleep(t)
    print('done %ds process' % t)
    return t

def cb(data):
    print('cb', data)

x = Pubsub(4)
x.on_finish_result(cb)
x.add_listener('event_1', test)
x.add_listener('event_1', test)
x.add_listener('event_1', test)
x.add_listener('event_1', test)
x.add_listener('event_1', test)

while True:
    try:
        print('emit event %d', random.random() * 3)
        x.emit('event_1', 'data')
        time.sleep(1)
    except KeyboardInterrupt:
        x.q.join()
        print('bye')
        exit()

