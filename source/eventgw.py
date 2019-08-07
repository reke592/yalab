#
# eventgw.py
#
# TODO:
#
import os
import secret
import socket
import struct
import threading
from cryptography.fernet import Fernet
from yalab import SocketEventGateway


# Transaction flow
#   client:
#       send DSDP to UDP multicast:
#           payload = client TCP port encrypted using public_key
#       on ACK:
#           if SERVER is None (meaning not connected to any Yalab server)
#           send HANDSHAKE enc_info enc_key
#       on HANDSHAKE: (received from server after sending client handshake)
#           validate signature
#           STOP sending DSDP iff status is OK
#       on received data:
#           validate encrypted message using signature
#           decrypt payload using symmetric key
#           process
#           response = pack_payload(event, reply)
#           encrypt response using NEW sym_key
#           encrypt key using public key
#           send enc_response and enc_key
#
#   server:
#       on DSDP: (received from client)
#           decrypt Client TCP port using private_key
#           connect to Client TCP port
#           send ACK with payload and signature (like telling the client to make a handshake)
#       on handshake:
#           decrypt client symmetric key using the private key
#           decrypt payload using client symmetric key
#           save client info
#           remember the client symmetric key for next request
#           send HANDSHAKE b'OK' signature 
#       on received data:
#           decrypt message using the private key
#           encrypt response using the client symmetric key
#           sign the encrypted message
#           send response with signature

#                          .------ payload -----.
#                         |                      |
#                      2 bytes                n bytes                      256 bytes
# big endian: | u_short event_id 65535 | variable_message | server signature or client_symmetric key
# sample:     |          1234          |        str       |         str to decrypt or verify
# output: (1234, b'str', b'str')
# event_id must be converted to 16bit wide big endian
#   event_id.to_bytes(2, byteorder='big')
payload_format = '>1H%ds'
def pack_payload(event_id: int, data):
    return struct.pack(payload_format % len(data), event_id, data)

def unpack_payload(raw):
    return struct.unpack(payload_format % (len(raw) - 2), raw)

packet_format = '>%ds256s'
def unpack(data):
    return struct.unpack(packet_format % (len(data) - 256), data)

def pack(payload, key_sig: bytes):
    fmt = packet_format % len(payload)
    return struct.pack(fmt, payload, key_sig)

def event_id(fn):
    def fget(self):
        #return fn().to_bytes(2, byteorder='big')
        return fn()
    def fset(self, v):
        raise TypeError('readonly')
    def fdel(self):
        raise TypeError('readonly')
    return property(fget, fset, fdel)


class Events(object):
    @event_id
    def OK_DONE():
        return 0

    @event_id
    def DSDP():
        return 1

    @event_id
    def ACK():
        return 2

    @event_id
    def HANDSHAKE():
        return 3

    @event_id
    def SERV_SHUTDOWN():
        return 999 

    @event_id
    def BLOCK():
        return 101

    @event_id
    def ALLOW():
        return 102

    @event_id
    def REDIRECT():
        return 201

# initialize for import
events = Events()

class YalabClientGateway(SocketEventGateway):
    def __init__(self, key_file: str = None):
        super(YalabClientGateway, self).__init__()
        if not  os.path.exists(key_file):
            raise ValueError("Key file not exist")
        else:
            # postcondition: may raise Exception
            secret.load_public_key(key_file)
            self._key = Fernet.generate_key()

    def on_receive(self, data, addr):
        try:
            payload, signature = unpack(data)
            secret.verify(payload, signature)
            payload = Fernet(self._key).decrypt(payload)
            # unpack payload structure
            event, data = unpack_payload(payload)
        except Exception as e: # dont emit
            print('something went wrong. %s' % e or 'Invalid payload')
            return (None, None)
        else:
            return (event, data)

    def on_reply(self, data, addr):
        self._key = Fernet.generate_key()
        payload = pack_payload(data[0], data[1])
        enc_payload = Fernet(self._key).encrypt(payload)
        enc_key = secret.encrypt(self._key)
        return pack(enc_payload, enc_key)


class YalabMasterGateway(SocketEventGateway):
    def __init__(self, key_file: str = None):
        super(YalabMasterGateway, self).__init__()
        if not os.path.exists(key_file):
            raise ValueError("Private Key not exist")
        else:
            self._clients = {}
            # postcondition: may raise Exception
            secret.load_private_key(key_file)

    def broadcast(self, event, data):
        print('broadcast')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            for IP in self._clients.keys():
                PORT = self._clients[IP]['tcp']
                print('sending broadcast to %s:%d' % (IP, PORT))
                if PORT:
                    key = self._clients[IP]['key']
                    payload = pack_payload(event, data)
                    enc_payload = Fernet(key).encrypt(payload)
                    sig = secret.sign(enc_payload)
                    s.connect((IP, PORT))
                    s.send(pack(enc_payload, sig))

    def on_receive(self, data, addr):
        try:
            enc_payload, enc_key = unpack(data)
            key = secret.decrypt(enc_key)
            payload = Fernet(key).decrypt(enc_payload)
            event, data = unpack_payload(payload)
        except Exception as e: #dont emit
            print('something went wrong. %s' % e or 'Invalid encryption')
            return (None, None)
        else:
            IP, PORT = addr 
            self._clients.setdefault(IP, {})
            self._clients[IP]['key'] = key
            if event == events.DSDP:
                self._clients[IP]['tcp'] = int.from_bytes(data, byteorder='big')
            return (event, (data, IP, key))

    def on_reply(self, data, addr):
        IP, PORT = addr
        key = self._clients[IP]['key']
        payload = pack_payload(data[0], data[1])
        enc_payload = Fernet(key).encrypt(payload)
        sig = secret.sign(enc_payload)
        return pack(enc_payload, sig)

