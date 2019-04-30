# pre-configuration for imports
import os
import sys
import time
import threading
import atexit

path = os.path
sleep = time.sleep
sys.path.insert(0, path.dirname(__file__))
sys.path.insert(0, path.join(path.dirname(__file__), 'classes'))
sys.path.insert(0, path.join(path.dirname(__file__), 'services'))

# ------ YALAB ------
import globals
globals.init()

# import yadb
# yadb.init()

import services.yalabdns as yalabdns
import services.blacklistd as blacklistd

a = yalabdns.Server()
b = blacklistd.Server()

a.start()
b.start()

def onExit():
    threading.Event.set(globals.EVENT_STOP_BLACKLISTD_SERVICE)
    threading.Event.set(globals.EVENT_STOP_DNS_SERVICE)
    a.join()
    b.join()

atexit.register(onExit)

while True:
    sleep(1)
