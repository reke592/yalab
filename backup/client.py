#
# yalab/bin/client.py
#
# OPTIONS:
#   -l --list           list clients
#
# OPTIONAL:
#   -s --static         show only static IP configured using 'client --add'
#   -d --dynamic        show only the clients known via UDP multicast
#   -a --active         show only active clients
#
# Usage:
#   client --list --active
#   client --list --dynamic
#   client --list --static
#   client -ldsa
#
# TODOi:
#   create function for --block, --allow, --redirect
#   OPTIMIZE sources [ client.py , ymaster.py ]
import argparse
import socket
import struct
import os
import re
from yconst import M_PACK, M_UNPACK, SO_EVENT_PACK, SO_EVENT_UNPACK, defaults
from key import const
from cryptography.fernet import Fernet
try:
    import cPickle as pickle
except:
    import pickle

STATIC_RECORDS = 'static.dat'
DYNAMIC_RECORDS = 'dynamic.dat'
DEFAULT_UDP_TIMEOUT = 0.3

def print_list(records):
    header_format = '%15s\t%15s'
    item_format = '%(ip)15s\t%(port)15d'
    count = len(records)
    print(header_format % ('ADDRESS', 'TCP_PORT'))
    for i in range(count):
        print(item_format % records[i])
    print('\nActive client(s): %d' % count) 


# records updated when adding or removing static client
def static_clients():
    try:
        with open(STATIC_RECORDS, 'rb') as f:
            return pickle.load(f)
    except:
        with open(STATIC_RECORDS, 'wb') as f:
            pickle.dump({}, f)
        return {}


# records updated when running --list
def dynamic_clients():
    try:
        with open(DYNAMIC_RECORDS, 'rb') as f:
            return pickle.load(f)
    except:
        with open(DYNAMIC_RECORDS, 'wb') as f:
            pickle.dump({}, f)
        return {}


def update_static_clients(argv):
    valid_format = re.compile(r'(?:\d{1,3}\.){3}(\d{1,3}):\d+')
    records = static_clients()
    if type(argv) is str:
        addrs = argv.split(',')
        for addr in addrs:
            if not ':' in addr:
                addr = addr + (':%d' % defaults.TCP_PORT)
            if not valid_format.match(addr):
                raise ValueError(addr)
            ip, port = addr.split(':')
            records[ip] = port
    elif type(argv) is list:
        for info in argv:
            records[info.get('ip')] = info.get('port')
    with open(STATIC_RECORDS, 'wb') as f:
        pickle.dump(records, f)


def remove_static_clients(argv):
    addrs = argv.split(',')
    existing = static_clients()
    count = 0
    for ip in addrs:
        try:
            del existing[ip]
            count = count + 1
        except:
            pass
    with open(STATIC_RECORDS, 'wb') as f:
        pickle.dump(existing, f)
    print('removed record(s): %d' % count)


def update_dynamic_clients(records):
    updates = {}
    for info in records:
        updates.setdefault(info['ip'], info['port'])
    with open(DYNAMIC_RECORDS, 'wb') as f:
        pickle.dump(updates, f)


def udp_ping_all(multicast_addr: tuple, timeout: float, szBuff: int, args):
    print('sending multicast to %s:%d' % multicast_addr)
    print('retrieving records... timeout: %.2fs\n' % timeout)
    clients = []
    header_format = '%15s\t%15s\t%15s\t%15s'
    item_format = '%(ip)15s\t%(port)15d\t%(iptype)15s\t%(remarks)15s'
    static_records = static_clients()
    static_updates = []
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        event = b'ping'
        payload = b'' # MUST be the yalabsvc config TCP_PORT
        ttl = struct.pack('b', 1)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        s.settimeout(timeout)
        message = SO_EVENT_PACK((event, payload))
        sig = const.secret.sign(message)
        s.sendto(M_PACK(defaults.MASTER_BIN_AGENT, sig, message), multicast_addr)
        print(header_format % ('ADDRESS', 'TCP_PORT', 'TYPE', 'REMARKS'))
        while True:
            try:
                data, addr = s.recvfrom(szBuff)
                if not data:
                    break
                enc_key, cipher = M_UNPACK(data)
                key = const.secret.decrypt(enc_key)
                f = Fernet(key)
                message = f.decrypt(cipher)
                event, payload = SO_EVENT_UNPACK(message)
                key, tcp_port = struct.unpack(defaults.HANDSHAKE_FORMAT, payload)
            except socket.timeout:
                #print('\ntimed out no more response to process.')
                break
            else:
                tcp_port = int.from_bytes(tcp_port, byteorder='big')
                static_record = static_records.get(addr[0])
                record = {
                    'ip': addr[0],
                    'port': tcp_port,
                    'iptype': 'STATIC' if static_record else 'DYNAMIC',
                    'remarks': 'UPDATED' if static_record and static_record != tcp_port else ''
                }
                if record.get('iptype') == 'STATIC' and static_records.get(addr[0]) != tcp_port:
                    static_updates.append(record)
                if args.static:
                    if record.get('iptype') == 'STATIC':
                        print(item_format % record)
                elif args.dynamic:
                    if record.get('iptype') == 'DYNAMIC':
                        print(item_format % record)
                else:
                    print(item_format % record)
                clients.append(record)
    print(header_format % ('--', '--', '--', '--'))
    print('\nActive client(s): %d' % len(clients))
    update_dynamic_clients(clients)
    update_static_clients(static_updates)
    return clients

def tcp_handshake(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    event = b'ping'
    sig = const.secret.sign(event)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(3)
        s.connect((ip,port))
        
        while True:
            data = s.recv(1024)
            if not data:
                break


def main(args):
    config = {}
    with open('yalabsvc.conf', 'r') as f:
        for line in f.readlines():
            k,v = line.strip('\n').split('=')
            config.setdefault(k, v)

    if args.list:
        multicast_ip = config.get('multicast')
        udp_port = int(config.get('port_udp'))
        udp_ping_all((multicast_ip, udp_port), args.timeout or DEFAULT_UDP_TIMEOUT, 1024, args)

    if args.save_static:
        update_static_clients(args.save_static)

    if args.remove_static:
        remove_static_clients(args.remove_static)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    opt = parser.add_mutually_exclusive_group()
    opt.add_argument('-l', '--list', action='store_true', help='list all active clients.')
    opt.add_argument('-S', '--save-static', type=str, help='save/update static client socket address. (eg. -s ip:port,ip:port)')
    opt.add_argument('-R', '--remove-static', type=str, help='remove static client. (eg. -r ip1,ip2,ip3)')
    parser.add_argument('-s', '--static', action='store_true', help='list static')
    parser.add_argument('-d', '--dynamic', action='store_true', help='list dynamic')
    parser.add_argument('-t', '--timeout', type=float, help='socket connection timeout in seconds. default %.2fs' % DEFAULT_UDP_TIMEOUT)
    # move to config.py
#    parser.add_argument('-b', '--block', type=str, help='block qname pattern on selected clients. (eg. --block abc.xyz,abc)')
#    parser.add_argument('-a', '--allow', type=str, help='allow / whitelist qname pattern on selected clients. (eg. --allow abc.xyz,abc)')
#    parser.add_argument('-r', '--redirect', type=str, help='add a hostfile entry on selected clients to redirect the qname to specific address. (eg. --redirect hostname@ip)')
    args = parser.parse_args()
    try:
        main(args)
    except Exception as e:
        print(e)
