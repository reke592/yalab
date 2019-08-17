#
# client.py
#
# TODO:
#   finish ClientGateway and UDPServer
#
from yalab import Pubsub, SocketEventGateway
from eventgw import events
import socket
import struct
import threading


class ClientUDPServer(threading.Thread):
    def __init__(self, address: str = None, timeout: int = 3, gatewayImpl: SocketEventGateway = None):
        if not gatewayImpl:
            raise ValueError('ClientUDPServer requires a SocketEventGateway instance')
        super(ClientUDPServer, self).__init__()
        self._gateway = gatewayImpl
        self.address = address
        self.port = self._gateway.udp_port
        self.mgrp = self._gateway.multicast_addr[0]
        self.alive = threading.Event()
        self.alive.set()
        self.connection_timeout = timeout
        self._atexit = None
        self._gateway = gatewayImpl

    def on(self, event, fn):
        self._gateway.on(event, fn)

    def emit(self, event, payload):
        self._gateway.emit(event, payload)

    def atexit(self, cb):
        T = type(cb).__name__
        if T != 'function' and T != 'method':
            raise ValueError('callback must be a function or method')
        self._atexit = cb

    def join(self, timeout=None):
        print('joining main thread')
        if self._atexit:
            print('executing atexit')
            self._atexit()
        # stop accepting request
        self.alive.clear()
        # wait for queued process
        self._gateway.join()
        self._socket.sendto(b'', self._servaddr)
        self._socket.close()
        threading.Thread.join(self, timeout)
        if not self.is_alive():
            print('reached target UDP server stopped.')
   
    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            SERV_ADDR = (self.address, self.port)
            GROUP = socket.inet_aton(self.mgrp)
            M_REQ = struct.pack('4sL', GROUP, socket.INADDR_ANY)
            s.bind(SERV_ADDR)
            s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, M_REQ)
            self._servaddr = SERV_ADDR
            self._socket = s
            print('UDP server started, listening on multicast %s:%d.' % (self.mgrp, self.port))
            while self.alive.is_set():
                print('UDP waiting to receive data')
                data, addr = s.recvfrom(1024)
                print('received %d bytes on UDP from %s:%d' % (len(data), addr[0], addr[1]))
                if data:
                    # to remove: must utilize the thread pool
                    worker = threading.Thread(target=self._gateway.process, args=(s, data, addr))
                    worker.start() 
               

class ClientTCPServer(threading.Thread):
    def __init__(self, address: str = '', backlog:int = 1, timeout:int = 3, gatewayImpl: SocketEventGateway = None):
        if not gatewayImpl:
            raise ValueError('ClientTCPServer requires a SocketEventGateway instance')
        super(ClientTCPServer, self).__init__()
        self._gateway = gatewayImpl
        self.port = self._gateway.tcp_port
        self.address = address
        self.connection_timeout = timeout
        self.backlog = backlog
        self.alive = threading.Event()
        self.alive.set()
        self._atexit = None

    def atexit(self, cb):
        T = type(cb).__name__
        if T != 'function' and T != 'method':
            raise ValueError('callback must be a function or method')
        self._atexit = cb

    def _worker(self, connection, addr, gateway: SocketEventGateway, timeout):
        print("accepted TCP socket connection from %s:%d" % addr)
        connection.settimeout(timeout)
        try:
            while True:
                data = connection.recv(1024)
                if not data:
                    print("socket connection %s:%d closed. NO_DATA" % addr)
                    break
                else:
                    print('received %d bytes from %s:%d' % (len(data), addr[0], addr[1]))
                    gateway.process(connection, data, addr)
        except socket.timeout:
            print("socket connection %s:%d closed. TIMEOUT" % addr)

    def on(self, event, fn):
        self._gateway.on(event, fn)

    def emit(self, event, payload):
        self._gateway.emit(event, payload)

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            SERV_ADDR = (self.address, self.port)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(SERV_ADDR)
            s.listen(self.backlog)
            self._servaddr = SERV_ADDR
            self._socket = s
            print('TCP server %s:%d started.' % SERV_ADDR)
            while self.alive.is_set():
                print('TCP waiting to receive data')
                con, addr = s.accept()
                con.settimeout(self.connection_timeout)
                # to remove: must utilize the thread pool
                worker = threading.Thread(target=self._worker, args=(con, addr, self._gateway, self.connection_timeout))
                worker.start()

    def join(self, timeout=None):
        print('joining main thread')
        if self._atexit:
            print('executing atexit')
            self._atexit()
        # stop accepting request
        self.alive.clear()
        # finish queued process
        self._gateway.join()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(self._servaddr)
        self._socket.close()
        threading.Thread.join(self, timeout)
        if not self.is_alive():
            print('reached target TCP server stopped.')
 

