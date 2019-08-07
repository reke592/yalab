#
# ~/yalab/services/yglobal.py
#
import threading
import logging

def init():
    global E_STOP_TCP
    global E_STOP_UDP
    global E_STOP_DNS
    global E_REQUIRE_LIST_UPDATE
    global E_REQUIRE_DNS_UPDATE
    global LOCK

    E_STOP_TCP = threading.Event()
    E_STOP_UDP = threading.Event()
    E_STOP_DNS = threading.Event()
    E_REQUIRE_LIST_UPDATE = threading.Event()
    E_REQUIRE_DNS_UPDATE = threading.Event()
    LOCK = threading.Lock()

    logging.basicConfig()
    logging.root.setLevel(logging.NOTSET)
#    logging.basicConfig(
#        format='%(asctime)s - %(message)s',
#        level=logging.DEBUG,
#        datefmt='%d-%b-%y %H:%M:%S'
#    )
