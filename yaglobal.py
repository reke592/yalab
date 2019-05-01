import threading
from classes.regexblocking import RegexBlocking


def init():
    # declaration
    global lock
    global blacklist
    global DNS_PORT
    global DNS_FORWARDER
    global DNS_HOST
    global EVENT_FETCH_UPDATES
    global EVENT_APPLY_UPDATES
    global EVENT_STOP_BLACKLISTD_SERVICE
    global EVENT_STOP_DNS_SERVICE
    global BLACKLIST_UPDATE_INTERVAL

    # definition
    lock = threading.Lock()
    blacklist = RegexBlocking()
    EVENT_FETCH_UPDATES = threading.Event()
    EVENT_APPLY_UPDATES = threading.Event()
    EVENT_STOP_BLACKLISTD_SERVICE = threading.Event()
    EVENT_STOP_DNS_SERVICE = threading.Event()
    BLACKLIST_UPDATE_INTERVAL = 5.0

    DNS_PORT = 53
    DNS_FORWARDER = '192.168.43.1'
    DNS_HOST = '127.0.0.1'
