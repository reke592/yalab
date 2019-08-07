#
# ymaster.py
#
from eventgw import YalabMasterGateway, events
from client import ClientTCPServer, ClientUDPServer
import atexit
import time

tcp_port = 10011
udp_port = 10021
multicast = '224.5.24.92'
gw = YalabMasterGateway('keys/sample_private.pem')

def handle_DSDP(data):
    return (events.ACK, tcp_port.to_bytes(2, byteorder='big')) 

def handle_SHUTDOWN(data):
    gw.broadcast(events.SERV_SHUTDOWN, data)

gw.on(events.DSDP, handle_DSDP)
gw.on(events.SERV_SHUTDOWN, handle_SHUTDOWN)

udp = ClientUDPServer(port=udp_port, address='', mgrp=multicast, gatewayImpl=gw)

udp.atexit(lambda: gw.emit(events.SERV_SHUTDOWN, b'bye'))
udp.start()


while True:
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        exit()
