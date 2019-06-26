#
# ~/yalab/services/ymaster.py
#
# TODO: serialize Server state for Master CLI
#
from cryptography.fernet import Fernet
from yconst import defaults as _Y, EventHandlerBase, SO_EVENT_PACK, SO_EVENT_UNPACK, M_PACK, M_UNPACK
import os
import logging
import ysecret
import yglobal as _G
import socket
import struct
import threading
import time
import sys

formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')

def setup_logger(name, log_file=None):
    global logger
    logger = logging.getLogger(name)
    if log_file:
        handler = logging.FileHandler(log_file)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

setup_logger('YMaster')

# controller for UDP socket events
class UDPController(EventHandlerBase):
    def __init__(self, state, lock):
        super(UDPController, self).__init__(state, lock)

    def on_ack(self, payload, addr, state, lock):
        logger.debug('received ACK from client on UDP socket from %s:%d' % addr)
        IP = addr[0]
        KEY, PORT = struct.unpack(_Y.HANDSHAKE_FORMAT, payload)
        PORT = int.from_bytes(payload, byteorder='big')
        lock.acquire()
        record = state['active_clients']
        record[IP] = (PORT, KEY)
        lock.release()
        pass 


# controller for TCP socket events
class TCPController(EventHandlerBase):
    def __init__(self, state, lock):
        super(TCPController, self).__init__(state, lock)

    # expect: payload = client TCP server port
    def on_connect(self, payload, addr, state, lock):
        logger.debug('received CONNECT from client on TCP socket from %s:%d' % addr)
        IP = addr[0]
        KEY, PORT = struct.unpack(_Y.HANDSHAKE_FORMAT, payload)
        PORT = int.from_bytes(payload, byteorder='big')
        lock.acquire()
        record = state['active_clients']
        record[IP] = (PORT, KEY)
        lock.release()
        return (b'ack', b'')


# Thread worker
# unpack client encrypted_key and message using M_UNPACK
# decrypt the encrypted_key using private_key to get the client symmetric_key
# decrypt the message using the client symmetric_key
# unpack the event, payload from message using SO_EVENT_UNPACK
# run controller.handle, result is tuple (event:bytes, payload:bytes)
# pack the message reply using SO_EVENT_PACK
# encrypt the message reply using client symmetric key
# sign the message reply using the private_key(reply, prehashed=True)
# pack the reply using M_PACK(sig, reply)
def tcp_socket_transaction(conn, addr, szBuff, controller):
    IP, PORT = addr
    logger.debug('Started transaction %s:%d.' % (IP, PORT))
    # start polling
    while True:
        try:
            data = conn.recv(szBuff)
            if not data:
                break
            # else
            encrypted_key, cipher = M_UNPACK(data)
            key = ysecret.decrypt(encrypted_key)
            f = Fernet(key)
            message = f.decrypt(cipher)
            event, payload = SO_EVENT_UNPACK(message)
        except socket.timeout:
            logger.debug('connection timedout on %s:%d.' % (IP, PORT))
            break
        else:
            logger.debug('received %d bytes from %s:%d.' % (len(data), IP, PORT))
            reply = controller.handle(event, payload, addr)
            if not reply:
                break
            # else
            encrypted_reply = f.encrypt(SO_EVENT_PACK(reply))
            sig = ysecret.sign(encrypted_reply, prehashed=True)
            conn.send(M_PACK(sig, encrypted_reply))
    conn.close()
    logger.debug('End transaction %s:%d.' % (IP, PORT))


def tcp_socket_listen(sock, szBuff, controller, alive, timeout):
    while True:
        conn, addr = sock.accept()
        debug_msg = 'accepted new TCP socket connection.' if alive.is_set() else 'stop TCP socket listen.'
        logger.debug(debug_msg)
        if alive.is_set():
            conn.settimeout(timeout)
            worker = threading.Thread(target=tcp_socket_transaction, args=(conn, addr, szBuff, controller))
            worker.start()
        else:
            break
    logger.debug('TCP socket stopped.')


def udp_socket_polling(sock, szBuff, controller):
    logger.debug('Started UDP socket polling.')
    # start polling
    while True:
        try:
            data, addr = sock.recvfrom(szBuff)
            if not data:
                break
            # else
            encrypted_key, cipher = M_UNPACK(data)
            key = ysecret.decrypt(encrypted_key)
            f = Fernet(key)
            message = f.decrypt(cipher)
            event, payload = SO_EVENT_UNPACK(message)
        except socket.timeout:
            logger.debug('timedout no more response on UDP socket.')
            break
        else:
            IP, PORT = addr
            logger.debug('received %d bytes from %s:%d.' % (len(data), IP, PORT))
            reply = controller.handle(event, payload, addr)
            if not reply:
                break
            # else
            encrypted_reply = f.encrypt(SO_EVENT_PACK(reply))
            sig = ysecret.sign(encrypted_reply, prehashed=True)
            conn.send(M_PACK(sig, encrpyted_reply))
    sock.close()
    logger.debug('Stopped UDP socket polling.')


class Server(threading.Thread):
    def __init__(self, tcp_port=None, szBuff=None, backlog=None, timeout=None, multicast_addr:tuple=None):
        super(Server, self).__init__()
        self.alive = threading.Event()
        self.alive.set()
        self.socket = None
        self.tcp_worker = None
        self.port = tcp_port
        logger.debug('config TCP port: %d' % tcp_port)
        self.backlog = backlog
        logger.debug('config Backlog: %d' % backlog)
        self.szBuff = szBuff
        logger.debug('config Buffer: %d' % szBuff)
        self.connection_timeout = timeout
        logger.debug('config TCP Connection timeout: %ds' % timeout)
        self.multicast_addr = multicast_addr
        logger.debug('config Multicast address: %s:%d' % multicast_addr)
        self.state = {
            'active_clients': {},
        }
        # the thread lock to update the Server state for each thread that handle the socket connection
        self.lock = threading.Lock()
        self.tcp_controller = TCPController(self.state, self.lock)
        self.udp_controller = UDPController(self.state, self.lock)

    def _ping_clients(self):
        if not self.multicast_addr:
            logger.debug('unable to ping clients, UDP multicast_addr not set')
        else:
            try:
                logger.debug('ping clients on multicast %s:%d' % self.multicast_addr)
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                ttl = struct.pack('b', 1)
                s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
                s.settimeout(0.2)
                event = b'ping'
                payload = self.port.to_bytes(2, byteorder='big')
                message = SO_EVENT_PACK((event, payload))
                sig = ysecret.sign(message, prehashed=True)
                s.sendto(M_PACK(sig, message), self.multicast_addr)
                worker = threading.Thread(target=udp_socket_polling, args=(s, self.szBuff, self.udp_controller))
                worker.start()
            except socket.timeout:
                logger.debug('UDP socket timedout no more response.') 
            except OSError as e:
                logger.debug(e)

    def _configure_tcp_socket(self):
        SERV_ADDR = ('', self.port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#       self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(SERV_ADDR)
        self.socket.listen(self.backlog)
        logger.debug('TCP server configured to listen on port %d' % self.port)
        self.tcp_worker = threading.Thread(target=tcp_socket_listen, args=(
            self.socket,
            self.szBuff,
            self.tcp_controller,
            self.alive,
            self.connection_timeout
        ))
        self.tcp_worker.start()

    # postcondition : spawn new Thread worker, target = socket_transaction 
    def run(self):
        self._configure_tcp_socket()
        self._ping_clients()
        while self.alive.is_set():
            time.sleep(1)


    def join(self, timeout=None):
        logger.debug('stopping TCP server.')
        self.alive.clear()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', self.port))
        self.socket.close()
        threading.Thread.join(self, timeout)
        if not self.is_alive():
            logger.debug('reached target TCP server stopped.')
