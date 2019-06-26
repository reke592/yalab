#
# ~/yalab/services/yclient.py
#
# TODO: serialize DNS blacklist for yalabdns startup
#
from yconst import defaults as _Y, CL_PACK, CL_UNPACK, SO_EVENT_PACK, SO_EVENT_UNPACK, EventHandlerBase
from cryptography.fernet import Fernet
import logging
import ysecret
import yglobal as _G
import os
import socket
import struct
import threading
import time

formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')

def setup_logger(name, log_file=None):
    global logger
    logger = logging.getLogger(name)
    if log_file:
        handler = logging.FileHandler(log_file)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

setup_logger('YClient')

# Master CLI socket connection handler
class TCPController(EventHandlerBase):
    def __init__(self, state, lock):
        super(TCPController, self).__init__(state, lock)

    def on_refresh(self, payload, addr, state, lock):
        logger.debug('received trigger to refresh DNS List')
        _G.LOCK.acquire()
        _G.E_REQUIRE_LIST_UPDATE.set()
        _G.LOCK.release()
        return (b'checksum', b'')

    def on_ack(self, payload, addr, state, lock):
        logger.debug('received master ACK from %s:%d.' % addr)
        return None


class UDPController(EventHandlerBase):
    def __init__(self, state, lock):
        super(UDPController, self).__init__(state, lock)

    def on_ping(self, payload, addr, state, lock):
        logger.debug('received master ping request from %s:%d.' % addr)
        MASTER_IP = addr[0]
        MASTER_PORT = int.from_bytes(payload, byteorder='big')
        # access server state
        lock.acquire()
        PORT = state['TCP_PORT']
        KEY = state['SYM_KEY']
        # update state master address
        state['MASTER_ADDR'] = (MASTER_IP, MASTER_PORT)
        lock.release()
        payload = struct.pack(_Y.HANDSHAKE_FORMAT, KEY, PORT.to_bytes(2, byteorder='big'))
        return (b'ack', payload)


# receive multicast data from UDP socket
# data is just a plain text with signature
# client reply will be encrypted using a generated symmetric key
# the symmetric key will be encrypted using the public_key
# the reply message is (encrypted_key, cipher)
# NO_LONG_POLLING
def udp_socket_listen(sock, szBuff, controller, alive):
    while True:
        try:
            logger.debug('UDP socket waiting to receive messesage.')
            data, addr = sock.recvfrom(szBuff)
        except Exception as e:
            logging.error(e)
        else:
            if alive.is_set():
                logger.debug('UDP socket received %d bytes from %s:%d' % (len(data), addr[0], addr[1]))
                if data: # process data, run controller.handle
                    sig, message = CL_UNPACK(data)
                    try:
                        ysecret.verify(message, sig)
                    except:
                        logger.debug('Invalid message signature from %s:%d.' % addr)
                    else:
                        event, payload = SO_EVENT_UNPACK(message)
                        reply = controller.handle(event, payload, addr)
                        if not reply:
                            raise Exception('no response for UDP event: on_%s' % event)
                        else:
                            key = Fernet.generate_key()
                            encrypted_key = ysecret.encrypt(key)
                            encrypted_message = Fernet(key).encrypt(SO_EVENT_PACK(reply))
                            sock.sendto(CL_PACK(encrypted_key, encrypted_message), addr)
            else:
                logger.debug('stop UDP socket listen.')
                break
    logger.debug('UDP socket stopped.')


def tcp_socket_listen(sock, szBuff, controller, alive, connection_timeout, state, lock):
    while alive.is_set():
        try:
            logger.debug('TCP socket waiting to receive connection.')
            conn, addr = sock.accept()
            conn.settimeout(connection_timeout)
        except Exception as e:
            logger.debug('Exception on thread tcp_socket_listen: %s' % e)
        else:
            if alive.is_set():
                # get Client SYM_KEY
                # this key is being fetched by master on events: master_udp.on_ack or master_tcp.on_connect 
                lock.acquire()
                key = state['SYM_KEY']
                lock.release()
                while True:
                    data = conn.recv(szBuff)
                    sig, message = CL_UNPACK(data)
                    logger.debug('TCP socket received %d bytes from %s:%d' % (len(data), addr[0], addr[1]))
                    try:
                        ysecret.verify(message, sig)
                        message = Fernet(key).decrypt(message)
                    except:
                        logger.debug('Invalid message from %s:%d.' % addr)
                        break # close connection
                    else:
                        event, payload = SO_EVENT_UNPACK(message)
                        reply = controller.handle(event, payload)
                        if not reply:
                            break
                        else:
                            key = Fernet.generate_key()
                            encrypted_message = Fernet(key).encrypt(SO_EVENT_PACK(reply))
                            encrypted_key = ysecret.encrypt(key)
                            conn.send(CL_PACK(encrypted_key, encrypted_message))
                # after polling        
                conn.close()
                # update Client SYM_KEY
                lock.acquire()
                state['SYM_KEY'] = key
                lock.release()
                logger.debug('TCP socket %s:%d connection closed.' % addr)
            else:
                logger.debug('stop TCP socket listen.')
                break
    logger.debug('TCP socket stopped.')
                 

class Server(threading.Thread):
    def __init__(self, tcp_port=None, udp_port=None, szBuff=None, multicast_group=None, timeout=None, master_ip=None, master_port=None):
        super(Server, self).__init__()
        self.alive = threading.Event()
        self.alive.set()
        self.tcp_socket = None
        self.udp_socket = None
        self.tcp_worker = None
        self.udp_worker = None
        self.tcp_port = tcp_port
        logger.debug('config TCP port: %d' % tcp_port)
        self.udp_port = udp_port
        logger.debug('config UDP port: %d' % udp_port)
        self.szBuff = szBuff
        logger.debug('config Buffer: %d' % szBuff)
        self.multicast_group = multicast_group
        logger.debug('config Multicast group: %s' % multicast_group)
        self.connection_timeout = timeout
        logger.debug('config TCP Connection timeout: %ds' % timeout)
        
        master_addr = None if not master_ip or not master_port else (master_ip, master_port) 
        logger.debug('config static Yalab Master IP: {}'.format(master_ip))
        logger.debug('config static Yalab Master PORT: {}'.format(master_port))
        self.state = {
            'TCP_PORT': self.tcp_port,
            'UDP_PORT': self.udp_port,
            'MULTICAST_GROUP': self.multicast_group,
            'SYM_KEY': Fernet.generate_key(),
            'MASTER_ADDR': master_addr 
        }
        self.lock = threading.Lock()
        self.tcp_controller = TCPController(self.state, self.lock)
        self.udp_controller = UDPController(self.state, self.lock) 

    def _configure_udp_socket(self):
        try:
            SERV_ADDR = ('', self.udp_port)
            GROUP = socket.inet_aton(self.multicast_group)
            M_REQ = struct.pack('4sL', GROUP, socket.INADDR_ANY)
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.bind(SERV_ADDR)
            self.udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, M_REQ)
        except OSError as e:
            logger.debug(e)
        else:
            self.udp_worker = threading.Thread(target=udp_socket_listen, args=(
                self.udp_socket,
                self.szBuff,
                self.udp_controller,
                self.alive
            ))
            self.udp_worker.start()

    def _configure_tcp_socket(self):
        try:
            SERV_ADDR = ('', self.tcp_port)
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.bind(SERV_ADDR)
            self.tcp_socket.listen(1)
        except Exception as e:
            logger.debug(e)
        else:
            self.tcp_worker = threading.Thread(target=tcp_socket_listen, args=(
                self.tcp_socket,
                self.szBuff,
                self.tcp_controller,
                self.alive,
                self.connection_timeout,
                self.state,
                self.lock
            ))
            self.tcp_worker.start()

    def try_connect(self):
        event = b'connect'
        PORT = self.state['TCP_PORT']
        KEY = self.state['SYM_KEY']
        payload = struct.pack(_Y.HANDSHAKE_FORMAT, KEY, PORT.to_bytes(2, byteorder='big'))
        try:
            self._tcp_try_send((event, payload))
        except Exception as e:
            logger.debug(e)

    def _tcp_try_send(self, data:tuple):
        self.lock.acquire()
        end_point = self.state['MASTER_ADDR']
        self.lock.release()
        if not end_point:
            logger.debug('static Yalab Master not configured. waiting for master UDP multicast.')
        else:
            logger.debug('connecting to master TCP socket %s:%d' % end_point)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                KEY = Fernet.generate_key()
                f = Fernet(KEY)
                encrypted_key = ysecret.encrypt(KEY)
                encrypted_message = f.encrypt(SO_EVENT_PACK(data))
                s.connect(end_point)
                s.send(CL_PACK(encrypted_key, encrypted_message))
                while True:
                    data = s.recv(self.szBuff)
                    if not data:
                        break
                    else:
                        try:
                            sig, message = CL_UNPACK(data)
                            ysecret.verify(message, sig)
                            message = f.decrypt(message)
                        except Exception as e:
                            logger.debug(e)
                        else:
                            event, payload = SO_EVENT_UNPACK(message)
                            reply = self.tcp_controller.handle(event, payload, end_point)
                            if reply:
                                self._tcp_try_send(reply)
                            else:
                                break # close the socket


    def run(self):
        self._configure_udp_socket()
        self._configure_tcp_socket()
        self.try_connect()
        while self.alive.is_set():
            if _G.E_REQUIRE_LIST_UPDATE.is_set():
                self.refresh_list()
            time.sleep(1)
            # so we can run the join on exit()

    # post-condition: TCP and UDP socket will stop, the Server thread will exit.
    def join(self, timeout=None):
        logger.debug('stopping client TCP and UDP sockets.')
        # break the TCP and UDP infinite-loop on next turn.
        self.alive.clear()
        # send some data to stop UDP socket waiting
        if self.udp_socket:
            self.udp_socket.sendto(b'', ('127.0.0.1', self.udp_port))
            self.udp_socket.close()
        # connect to stop TCP socket waiting
        if self.tcp_socket:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('127.0.0.1', self.tcp_port))
            self.tcp_socket.close()
        threading.Thread.join(self, timeout)
        if not self.is_alive():
            logger.debug('reached target yalab client server stopped.')

    def refresh_list(self):
        logger.debug('fetching updated list from master')
        _G.LOCK.acquire()
        _G.E_REQUIRE_LIST_UPDATE.clear()
        _G.LOCK.release()
