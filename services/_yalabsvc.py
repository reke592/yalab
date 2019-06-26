# Yalab service
import argparse
import os
import re
import sys
import socket
import time
import ysecret
import yglobal
import ymaster as master
import yclient as client
import yalabdns
from yconst import defaults
from getpass import getpass

parser = argparse.ArgumentParser(prog='yalabsvc',
                                 description='YALAB service for client-server connection.')

parser.add_argument('--key-generate', type=str,
                    help='create a RSA keys. argv = prefix for key files.')

parser.add_argument('--key-import', type=str, help='import public key file.')

parser.add_argument('--key', type=str, help='use private key.')

parser.add_argument('--key-list', action='store_true', help='list generated private keys.')

parser.add_argument('--master-ip', type=str, help='set static Yalab Master IP.')

parser.add_argument('--master-port', type=int, help='set static Yalab Master TCP PORT.')

parser.add_argument('-tcp', '--port-tcp', type=int, default=None,
                    help='set client/server TCP socket port. default: client:%d, master:%d' % (defaults.TCP_PORT, defaults.MASTER_TCP_PORT))

parser.add_argument('-udp', '--port-udp', type=int, default=defaults.UDP_PORT,
                    help='set client/server UDP socket port. default %d.' % defaults.UDP_PORT)

parser.add_argument('--multicast', type=str, default=defaults.MULTICAST_GROUP,
                    help='set the master UDP multicast group.')

parser.add_argument('-r', '--run', action='store_true',
                    help='start main loop.')

parser.add_argument('--buffer', type=int, default=defaults.SOCK_SZBUFF,
                    help='set socket.recv buffer size. default %d.' % defaults.SOCK_SZBUFF)

parser.add_argument('--backlog', type=int, default=1,
                    help='set socket backlog. default 1.')

parser.add_argument('--timeout', type=int, default=10,
                    help='set socket connection timeout. default 10s')

serve_type = parser.add_mutually_exclusive_group()

serve_type.add_argument('--master', action='store_true',
                        help='run as Master, can control client DNS blocking.')
serve_type.add_argument('--client', action='store_true',
                        help='run as Client, block everything declared by master.')

args = parser.parse_args()

def configure():
    if args.key_list:
        print('List of generated private keys:')
        keys = os.listdir(defaults.DIR_KEYS)
        pattern = re.compile('.+_private\.pem$')
        for key in keys:
            if pattern.match(key):
                print(key[0:-12])   # _private.pem = 12 chars


    if not os.path.exists(defaults.DIR_KEYS):
        os.mkdir(defaults.DIR_KEYS)

    if not os.path.exists(defaults.DIR_DATA):
        os.mkdir(defaults.DIR_DATA)

    # TODO: add to passwd dictionary, dump data to passwd.dat, data MUST be encrypted using AES256
    # passphrase = host MAC processed by an algorithm
    if args.key_generate:
        password = getpass('Enter password for %s:' % args.key_generate)
        ysecret.create_keys(
            directory=defaults.DIR_KEYS,
            name=args.key_generate,
            password=password or ''
        )
        if password:
            #TODO: create algo to serialize password
            print('created new encrypted private key: %s' % args.key_generate)
            pass
        else:
            print('createed non-encrypted private key: %s' % args.key_generate)

    if args.key_import:
        if not os.path.exists(args.key_import):
            raise ValueError('%s not found' % args.key_import)
        with open(args.key_import, 'rb') as key_file:
            with open(os.path.join(defaults.DIR_KEYS, defaults.IMPORTED_PUBLIC_KEY_FILE), 'wb') as copy_file:
                copy_file.write(key_file.read())


# server modes
def run():
    if not args.master and not args.client:
        print('Server mode not set. select either --master or --client.')
    # Yalab Master, we always use the generated private key
    if args.master:
        # create signature file using --password
        if not args.key:
            raise Exception('Error: Yalab Master requires a private key.')
        else:
            key_file = os.path.join(defaults.DIR_KEYS, args.key + '_private.pem')
            ysecret.load_private_key(key_file)
            server = master.Server(
                tcp_port = args.port_tcp or defaults.MASTER_TCP_PORT,
                multicast_addr = (args.multicast, args.port_udp),
                szBuff = args.buffer,
                backlog = args.backlog,
                timeout = args.timeout
            )
            server.start()
    # Yalab Client, will use the imported public key file to validate the incoming data and encrypt the response
    elif args.client:
        key_file = os.path.join(defaults.DIR_KEYS, defaults.IMPORTED_PUBLIC_KEY_FILE)
        if not os.path.exists(key_file):
            raise Exception('Error: Yalab Client requires a public key. use --key-import PUBLIC_KEY_FILE')
        else:
            ysecret.load_public_key(key_file)
            server = client.Server(
                tcp_port = args.port_tcp or defaults.TCP_PORT,
                udp_port = args.port_udp or defaults.UDP_PORT,
                multicast_group = args.multicast,
                szBuff = args.buffer,
                timeout = args.timeout,
                master_ip = args.master_ip,
                master_port = args.master_port
            )
            server.start()
            # YalabDNS Server
            dns_server = yalabdns.Server()
            if not os.path.exists('./data/intercept'):
                os.makedirs('./data/intercept')
            dns_server.add_interceptor(yalabdns.RegexInterceptor('./data/intercept/allow.list', block=False), priority=0)
            dns_server.add_interceptor(yalabdns.RegexInterceptor('./data/intercept/deny.list'))
            dns_server.add_interceptor(yalabdns.HostFileInterceptor('./data/intercept/hostfile'), priority=1)
            dns_server.start()

def main_loop():
    if args.run:
        try:
            run()
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            exit()
        except Exception as e:
            print(e)
            exit()

if __name__ == '__main__':
    yglobal.init()
    configure()
    main_loop()
