#
# ymaster.py
#
# TODO: connect the UI
# no need to provide reply token, just include the client reply_token when signing reply
# always update client reply_token
#
from cryptography.fernet import Fernet
from eventgw import events, pack, unpack, pack_payload, unpack_payload, unpack_handshake
from client import ClientTCPServer, ClientUDPServer
from yalab import SocketEventGateway
import secret
import socket
import atexit
import time
import os

class YalabMasterGateway(SocketEventGateway):
    def __init__(self, key_file: str = None):
        super(YalabMasterGateway, self).__init__(worker_ct=2)
        if not os.path.exists(key_file):
            raise ValueError("Private Key not exist")
        else:
            self._clients = {}
            # postcondition: may raise Exception
            secret.load_private_key(key_file)
            self.on(events.DSDP, self.__handle_DSDP)
            self.on(events.HANDSHAKE, self.__handle_HANDSHAKE)
            self.on(events.SERV_SHUTDOWN, self.__handle_SERV_SHUTDOWN)

    def __handle_HANDSHAKE(self, data):
        print('Received handshake request')
        enc_payload, key, addr = data
        IP, PORT = addr
        if self._clients.get(IP):
            raise Exception('Client %s has an active handshake' % IP)
        # else proceed to handshake
        payload = Fernet(key).decrypt(enc_payload)
        tcp_port, identity, reply_token = unpack_handshake(payload)
        self._clients.setdefault(IP, {
            'key': key,
            'tcp': tcp_port,
            'identity': identity,
            'shutdown_signal': lambda _ : self.inform_disconnect(addr[0], events.SERV_SHUTDOWN, _),
            'reply_token': secret.decrypt(reply_token)
        })
        # add client to signal, so we inform then on __SHUTDOWN__ event 
        self.on('__SHUTDOWN__', self._clients.get(IP)['shutdown_signal'])
        # send success to client
        print('Client %s handshake accepted.' % IP)
        self.make_response(events.HANDSHAKE, b'succes', self._clients.get(IP)['reply_token'], addr)

    # TODO: secure this by token validation
    def __handle_SERV_SHUTDOWN(self, data):
        enc_message, reply_token, addr = data
        record = self._clients.get(addr[0])
        if record:
            if record.get('reply_token') == reply_token:
                print('received client shutdown signal from %s' % addr[0])
                self.remove_listener('__SHUTDOWN__', record['shutdown_signal'])
                del self._clients[addr[0]]
            else:
                print('Unable to release %s handshake. Invalid client_token.' % addr[0])

    def __handle_DSDP(self, received):
        payload, reply_token, addr = received 
        if not self._clients.get(addr[0]):
            data = self.tcp_port.to_bytes(2, byteorder='big')
            self.make_response(events.ACK, data, reply_token, addr)
        else:
            print('Ignore DSDP request from %s. ACK already sent.' % addr[0])

    def inform_disconnect(self, ip, event, data):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            record = self._clients.get(ip)
            if record:
                port = record.get('tcp') or record.get('udp')
                key = record.get('key')
                reply_token = record.get('reply_token')
                if not port or not key or not reply_token:
                    raise ValueError('No handshake record for %s' % ip)
                print('informing client %s:%d' % (ip, port))
                payload = pack_payload(event, data)
                enc_payload = Fernet(key).encrypt(payload)
                sig = secret.sign(enc_payload + reply_token)
                try:
                    s.connect((ip, port))
                except Exception as e:
                    print('unable to send information to %s:%d. %s.' % (ip, port, e))
                else:
                    s.send(pack(enc_payload, sig))

    def on_receive(self, received):
        try:
            data, addr = received
            message, enc_info = unpack(data)
            event, payload = unpack_payload(message)
            other = secret.decrypt(enc_info)
        except Exception as e:
            print('Error: %s' % type(e))
            return
        else:
            self.emit(event, (payload, other, addr))

    def make_response(self, event, data, reply_token, addr):
        self.emit('__RESPONSE__', ((event, data), reply_token, addr))
   
    def on_reply(self, response):
        if not response:
            return
        try:
            data, reply_token, addr = response
            IP, PORT = addr
            payload = pack_payload(data[0], data[1])
            key = self._clients[IP]['key']
            enc_payload = Fernet(key).encrypt(payload)
        except Exception as e:
            print('Sending non encrypted reply to %s. Gateway Event: %d' % (IP, data[0]))
            reply = pack(payload, secret.sign(payload + reply_token))
        else:
            reply = pack(enc_payload, secret.sign(enc_payload + reply_token))
        finally:
            self.emit('__SEND_REPLY__', (reply, addr))


tcp_port = 10010
udp_port = 10021
multicast = '224.5.24.92'
gw = YalabMasterGateway('keys/sample_private.pem')
gw.configure(tcp=tcp_port, udp=udp_port, multicast_group=multicast, dsdp_interval=3)

tcp = ClientTCPServer(address='', gatewayImpl=gw)
udp = ClientUDPServer(address='', gatewayImpl=gw)

udp.atexit(lambda: gw.emit('__SHUTDOWN__', b'server shutdown'))
udp.start()
tcp.start()

while True:
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        exit()
