#
# yclient.py
#
from cryptography.fernet import Fernet
from eventgw import YalabClientGateway, events, pack, unpack, pack_payload, unpack_payload
from client import ClientTCPServer
import secret
import socket
import struct
import time
import threading

tcp_port = 10011
udp_port = 10021
multicast = '224.5.24.92'
gw = YalabClientGateway('keys/sample_public.pem')


def _DSDP(multicast_addr, payload, timeout, interval):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        ttl = struct.pack('b', 1)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        s.settimeout(timeout)
        payload = pack_payload(events.DSDP, payload)
        enc_payload = Fernet(gw._key).encrypt(payload)
        enc_key = secret.encrypt(gw._key)
        print('%s waiting for server. interval %ds' % (time.time(), interval))
        while True:
            s.sendto(pack(enc_payload, enc_key), multicast_addr)
            try:
                data, addr = s.recvfrom(1024)
                enc_payload, sig = unpack(data)
                secret.verify(enc_payload, sig)
                event, payload = unpack_payload(Fernet(gw._key).decrypt(enc_payload))
            except socket.timeout:
                pass
            else:
                if event == events.ACK:
                    print('%s found server %s:%d' % (time.time(), addr[0], int.from_bytes(payload, byteorder='big')))
                    break
            time.sleep(interval)
 

def handle_DSDP(data):
    multicast_addr, payload = data
    timeout = 1 
    interval = 3
    worker = threading.Thread(target=_DSDP, args=(multicast_addr, payload, timeout, interval), daemon=True) 
    worker.start()

def handle_SERV_SHUTDOWN(data):
    print('Endpoint server has shutdown')
    gw.emit('DSDP', (multicast_addr, tcp_port.to_bytes(2, byteorder='big')))


multicast_addr = (multicast, udp_port)
gw.on('DSDP', handle_DSDP)
gw.on(events.SERV_SHUTDOWN, handle_SERV_SHUTDOWN)

tcp = ClientTCPServer(port=tcp_port, address='', gatewayImpl=gw)
tcp.start()

gw.emit('DSDP', (multicast_addr, tcp_port.to_bytes(2, byteorder='big')))

while True:
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        exit()

