#
# yclient.py
#
# TODO: inform server on client shutdown
#
from cryptography.fernet import Fernet
from eventgw import events, pack_handshake, pack_payload, unpack_payload, pack, unpack
from yalab import SocketEventGateway
from client import ClientTCPServer
import secret
import socket
import struct
import threading
import time
import os

class YalabClientGateway(SocketEventGateway):
    def __init__(self, key_file: str = None):
        super(YalabClientGateway, self).__init__()
        if not  os.path.exists(key_file):
            raise ValueError("Key file not exist")
        else:
            secret.load_public_key(key_file)
            self._key = Fernet.generate_key()
            self._identity = secret.encrypt(secret._sys_info())
            self._master_ip = None
            self._master_tcp_port = None
            self._master_disconnect = None
            self._lock = threading.Lock()
            self._dsdp_event = threading.Event()
            self._dsdp_event.set()
            self.on(events.SERV_SHUTDOWN, self.__handle_DSDP_RESTART)
            self.on(events.ACK, self.__handle_ACK)
            self.on(events.HANDSHAKE, self.__handle_HANDSHAKE)
            # start dsdp
    
    def start_dsdp(self, interval, daemon=False):
        self.dsdp_interval = interval
        self._dsdp_alive = threading.Event()
        self._dsdp_alive.set()
        self._dsdp_worker = threading.Thread(target = self._dsdp_task, daemon=daemon, args=(self._dsdp_alive, self._dsdp_event, b'hello', interval))
        self._dsdp_worker.start()
        print('DSDP %s started.' % ('daemon thread' if daemon else 'thread'))
        if not daemon:
            self.on('__SHUTDOWN__', lambda _ : self.stop_dsdp())

    def stop_dsdp(self, timeout=None):
        try:
            print('send shutdown signal to DSDP thread')
            self._dsdp_event.clear()
            self._dsdp_alive.clear()
            self._dsdp_worker.join(timeout)
        except Exception as e:
            print('Unable to send shutdown signal to DSDP thread. %s: %s' % (type(e), e))

    def __handle_ACK(self, data):
        payload, addr = data 
        print('received ACK from %s' % addr[0])
        self._dsdp_event.clear()
        self._master_tcp_port = int.from_bytes(payload, byteorder='big')
        self._master_ip = addr[0]
        SERV_ADDR = (self._master_ip, self._master_tcp_port)
        self.send_handshake_to(SERV_ADDR)

    def __handle_DSDP_RESTART(self, message):
        # always clear master_disconnect from __SHUTDOWN__ event to avoid sending multiple disconnect signal
        try:
            self.remove_listener('__SHUTDOWN__', self._master_disconnect)
            print('Released server shutdown hook.')
        except:
            pass
        finally:
            self._dsdp_event.set()
            print('DSDP start sending packets.')

    def _dsdp_task(self, t_alive, t_event, payload, interval):
            while t_alive.is_set():
                try:
                    if t_event.is_set():
                        self.send_to_multicast(payload, 0.3)
                except Exception as e:
                    print('Unable to send DSDP request. %s.' % e)
                finally:
                    time.sleep(interval)
            print('DSDP thread stopped.')

    def __handle_HANDSHAKE(self, data):
        data, addr = data
        print('received handshake response from %s:%d' % addr) 
        SERV_ADDR = (self._master_ip, self._master_tcp_port)
        self._master_disconnect = lambda _ : self.inform_disconnect(SERV_ADDR, events.SERV_SHUTDOWN, _ )
        self.on('__SHUTDOWN__', self._master_disconnect)

    def send_to_multicast(self, payload, t=None):
        print('sent data to UDP')
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            ttl = struct.pack('b', 1)
            s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
            s.settimeout(t)
            payload = Fernet(self._key).encrypt(payload)
            message = pack_payload(events.DSDP, payload)
            data = pack(message, self._reply_token())
            s.sendto(data, self.multicast_addr)
            while True:
                try:
                    data, addr = s.recvfrom(1024)
                    self.process(s, data, addr)
                except socket.timeout:
                    #print('no more response')
                    break
                except:
                    print('Invalid DSDP response from %s' % addr[0])
                    break

    def send_handshake_to(self, addr):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            payload = pack_handshake(self.tcp_port, bytes(secret._sys_info(), encoding='utf-8'), self._reply_token())
            print('TCP send handshake')
            enc_payload = Fernet(self._key).encrypt(payload)
            message = pack_payload(events.HANDSHAKE, enc_payload)
            data = pack(message, secret.encrypt(self._key))
            s.settimeout(0.3)
            s.connect(addr)
            s.send(data)
            while True:
                try:
                    data = s.recv(1024)
                    self.process(s, data, addr)
                except socket.timeout:
                    print('no more response')
                    break
                except:
                    print('Invalid handshake response from %s' % addr[0])
                    break

    def inform_disconnect(self, addr, event, payload):
        if not self._master_ip:
            return
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            print('informing master %s:%d' % addr)
            try:
                payload = Fernet(self._key).encrypt(payload)
                message = pack_payload(event, payload)
                data = pack(message, secret.encrypt(self._current_token))
                s.connect(addr)
            except Exception as e:
                print('unable to send information to %s:%d. %s.' % (addr[0], addr[1], type(e)))
            else:
                s.send(data)
                self._master_ip = None

    def on_receive(self, received):
        try:
            data, addr = received
            message, signature = unpack(data)
            secret.verify(message + self._current_token, signature)
            payload = Fernet(self._key).decrypt(message)
        except Exception as e: # if the message is not encrypted ( Handshake response from master is not encrypted using self._key )
            event, data = unpack_payload(message)
            # only reply to ACK from master server
            if event == events.ACK:
                self.emit(event, (data, addr))
            else:
                print('something went wrong. %s' % type(e))
        else:
            # unpack payload structure
            event, data = unpack_payload(payload)
            self.emit(event, (data, addr))

    def _reply_token(self, n=16):
        token = os.urandom(n)
        self._current_token = token
        return secret.encrypt(token)

    def make_response(self, event, data, addr):
        self.emit('__RESPONSE__', ((event, data), addr))

    def on_reply(self, response):
        data, addr = response
        payload = Fernet(self._key).encrypt(data[1])
        message = pack_payload(data[0], payload)
        reply = pack(message, self._reply_token())
        self.emit('__SEND_REPLY__', (reply, addr))


def main(args):
    try:
        tcp_port = args.tcp
        udp_port = args.udp
        mgrp = args.mgrp
        key = args.key
        dsdp_t = args.dsdp_interval
        gw = YalabClientGateway(key)
        gw.configure(
            tcp = tcp_port,
            udp = udp_port,
            multicast_group = mgrp
        )
        tcp_serv = ClientTCPServer(gatewayImpl=gw)
        tcp_serv.atexit(lambda: gw.emit('__SHUTDOWN__', b'0'))
    
    except Exception as e:
        print('Error: %s.' % e)
    else:
        tcp_serv.start()
        gw.start_dsdp(dsdp_t)
        while True:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                exit()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--tcp', type=int, default=10020, help='set tcp port.')
    parser.add_argument('--udp', type=int, default=10021, help='set udp port.')
    parser.add_argument('--mgrp', type=str, default='224.5.24.92', help='set multicast group.')
    parser.add_argument('--key', type=str, default='', help='path to RSA public key.')
    parser.add_argument('--dsdp-interval', type=int, default=3, help='DSDP interval when waiting for master server.')
    args = parser.parse_args()
    main(args)

