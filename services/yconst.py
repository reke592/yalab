#
# ~/yalab/services/yconst.py
#
import os
import socket
import struct
import logging
import threading

def constant(f):
    def fget(self):
        return f()

    def fset(self, v):
        raise TypeError('readonly')

    def fdel(self):
        raise TypeError('readonly')

    return property(fget, fset, fdel)


class _Const():
    @constant
    def MULTICAST_GROUP():
        return '224.5.24.92'

    @constant
    def TCP_PORT():
        return 10001

    @constant
    def MASTER_TCP_PORT():
        return 10000

    @constant
    def UDP_PORT():
        return 10021

    @constant
    def TCP_TIMEOUT():
        return 2

    @constant
    def UDP_TIMEOUT():
        return 0.2

    @constant
    def DIR_DATA():
        return os.path.join(os.path.dirname(__file__), 'data')

    @constant
    def DIR_KEYS():
        return os.path.join(os.path.dirname(__file__), 'keys')

    # generic name for imported public key
    @constant
    def IMPORTED_PUBLIC_KEY_FILE():
        return 'public_key.pem'

    @constant
    def PASSWD_FILE():
        return 'yalab.dat'

    # list of MAC and TCP PORT of clients
    @constant
    def DATA_FILE_CLIENT_LIST():
        return 'clients.dat'

    # list of clients who respond to UDP broadcast
    # file is deleted on service restart or explicit CLI command
    # contains all client's runtime key to start communication over TCP using symmetric encryption
    @constant
    def DATA_FILE_ACTIVE_CLIENTS():
        return 'active.dat'

    @constant
    def SEPARATOR():
        return ':'

    # Yalab MAX_LEN for socket event_name
    # default 8
    @constant
    def EVENT_LEN():
        return 8

    # signature length
    @constant
    def SIG_LEN():
        return 256

    # 44s plain symmetric key
    # 2s TCP socket port bytecount 2, byteorder 'big'
    @constant
    def HANDSHAKE_FORMAT():
        return '44s2s'

    @constant
    def SOCK_SZBUFF():
        return 1024

# initialize defaults
defaults = _Const()


# bytestream subject for encryption algorithm
def SO_EVENT_PACK(reply : tuple):
    event, payload = reply
    fmt = '8s%ds' % len(payload)
    return struct.pack(fmt, event, payload)


# unpack where message is decrypted bytestream
def SO_EVENT_UNPACK(message : bytes):
    message_len = len(message) - defaults.EVENT_LEN
    fmt = '8s%ds' % message_len 
    event, payload = struct.unpack(fmt, message)
    event = event.strip(b'\x00')
    return (event, payload)


# YMaster pack before sending to client socket
def M_PACK(sig, encrypted_stream):
    fmt = '256s%ds' % len(encrypted_stream)
    return struct.pack(fmt, sig, encrypted_stream)


# Ymaster unpack cipher subject for decryption
# 256 RSA encrypted client symmetric key
def M_UNPACK(raw):
    message_len = len(raw) - defaults.SIG_LEN
    fmt = '256s%ds' % message_len
    return struct.unpack(fmt, raw)


# YClient pack before sending to master
def CL_PACK(encrypted_key, encrypted_stream):
    fmt = '256s%ds' % len(encrypted_stream)
    return struct.pack(fmt, encrypted_key, encrypted_stream)


# YClient unpack subject for verification and decryption
def CL_UNPACK(raw):
    message_len = len(raw) - defaults.SIG_LEN
    fmt = '256s%ds' % message_len 
    return struct.unpack(fmt, raw)


class EventHandlerBase(object):
    def __init__(self, state, lock):
        setattr(self, '__state', state)
        setattr(self, '__lock', lock)


    def _on_secret(self, payload, addr, state, lock):
        return None


    def handle(self, event, payload, addr):
        try:
            event = event.decode('utf_8')
            handler = 'on_' + event
            if not hasattr(self, handler):
                fn = getattr(self, '_on_secret')
            else:
                fn = getattr(self, 'on_' + event)
            state = getattr(self, '__state')
            lock = getattr(self, '__lock')
        except:
            raise Exception('not implemented event', 'on_' + event)
        else:
            return fn(payload, addr, state, lock)
        
