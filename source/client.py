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
    def __init__(self, port: int = 0, mgrp: str = None, address: str = None, timeout: int = 3, gatewayImpl: SocketEventGateway = None):
        super(ClientUDPServer, self).__init__()
        self.address = address
        self.port = port
        self.mgrp = mgrp
        self.alive = threading.Event()
        self.alive.set()
        self._gateway = gatewayImpl
        self.connection_timeout = timeout
        self._atexit = None

    def on(self, event: str, fn):
        self._gateway.on(event, fn)

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
        self.alive.clear()
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
                print('waiting to receive data')
                data, addr = s.recvfrom(1024)
                if data:
                    worker = threading.Thread(target=self._gateway.process, args=(s, data, addr))
                    worker.start() 
               

class ClientTCPServer(threading.Thread):
    def __init__(self, port: int = 0, address: str = '', backlog:int = 1, timeout:int = 3, gatewayImpl: SocketEventGateway = None):
        super(ClientTCPServer, self).__init__()
        self.port = port
        self.address = address
        self.connection_timeout = timeout
        self.backlog = backlog
        self.alive = threading.Event()
        self.alive.set()
        self._gateway = gatewayImpl
        self._atexit = None

    def atexit(self, cb):
        T = type(cb).__name__
        if T != 'function' and T != 'method':
            raise ValueError('callback must be a function or method')
        self._atexit = cb

    def _worker(self, connection, addr, gateway: SocketEventGateway, timeout):
        print("accepted socket connection from %s:%d" % addr)
        connection.settimeout(timeout)
        try:
            while True:
                data = connection.recv(1024)
                if not data:
                    print("socket connection %s:%d closed. NO_DATA" % addr)
                    break
                else:
                    gateway.process(connection, data, addr)
        except socket.timeout:
            print("socket connection %s:%d closed. TIMEOUT" % addr)

    def on(self, event: str, fn):
        self._gateway.on(event, fn)

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
                print('waiting to receive data')
                con, addr = s.accept()
                con.settimeout(self.connection_timeout)
                worker = threading.Thread(target=self._worker, args=(con, addr, self._gateway, self.connection_timeout))
                worker.start()

    def join(self, timeout=None):
        print('joining main thread')
        if self._atexit:
            print('executing atexit')
            self._atexit()
        self.alive.clear()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(self._servaddr)
        self._socket.close()
        threading.Thread.join(self, timeout)
        if not self.is_alive():
            print('reached target TCP server stopped.')
 

