#
# eventgw.py
#
# TODO:
#
import os
import re
import secret
import socket
import struct
import time
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

handshake_format = '>1H%ds256s'
def pack_handshake(tcp_port, identity, reply_token):
    return struct.pack(handshake_format % len(identity), tcp_port, identity, reply_token)

def unpack_handshake(raw):
    return struct.unpack(handshake_format % (len(raw) - 258), raw)

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
    # [ not yet implemented ] emitted by master, sent to client TCP : in response to HANDSHAKE request
    @event_id
    def OK_DONE():
        return 0

    # emitted by clients, sent to master UDP
    @event_id
    def DSDP():
        return 1

    # emitted by master, sent to client UDP : in response to DSDP
    @event_id
    def ACK():
        return 2

    # [ not yet implemented ] emitted by clients, sent to master : to initiate eliptic curve
    @event_id
    def HANDSHAKE():
        return 3

    # emitted by master, broadcast to clients TCP
    @event_id
    def SERV_SHUTDOWN():
        return 5 

    # emitted by client, sent to master TCP
    @event_id
    def CLIENT_RESTART():
        return 6

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
 
