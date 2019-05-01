import atexit
import os
import sys
import threading
import time
import yaglobal
try:
    yaglobal.init()
    from yaglobal import EVENT_STOP_BLACKLISTD_SERVICE, EVENT_STOP_DNS_SERVICE
    import services.blacklistd as blacklistd
    import services.yalabdns as yalabdns
except Exception as e:
    print('Error while importing:', e)
    pass

# path configuration for imports
path = os.path
sleep = time.sleep
sys.path.insert(0, path.dirname(__file__))
sys.path.insert(0, path.join(path.dirname(__file__), 'classes'))
sys.path.insert(0, path.join(path.dirname(__file__), 'services'))

if __name__ == "__main__":
    # ------ YALAB Daemon services------
    a = yalabdns.Server()
    b = blacklistd.Server()

    # start services
    a.start()
    b.start()

    # make sure daemon services shutdown gracefully.
    def onExit():
        threading.Event.set(yaglobal.EVENT_STOP_BLACKLISTD_SERVICE)
        threading.Event.set(yaglobal.EVENT_STOP_DNS_SERVICE)
        a.join()
        b.join()

    atexit.register(onExit)

    # keep alive main-thread
    while True:
        sleep(1)
