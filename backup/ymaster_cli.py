import argparse
import os
import socket
import ysecret
from yalabsvc import DEFAULT_KEY_LOCATION, DEFAULT_PRIVATE_KEY_FILE, CLIENT_LIST
try:
    import cPickle as pickle
except:
    import pickle

parser = argparse.ArgumentParser()

target = parser.add_mutually_exclusive_group()
target.add_argument('--host',
                    help="PC hostname, separated by ',' for multiple entries.")
target.add_argument('--ip',
                    help="PC IP address, separated by ',' for multiple entries.")
target.add_argument('-a', '--all', action='store_true',
                    help='apply to all clients.')


action = parser.add_mutually_exclusive_group()
action.add_argument('--block',
                    help="domain name or pattern to block. separated by ',' for multiple entries.")
action.add_argument('--allow',
                    help="domain name or pattern to block. separated by ',' for multiple entries.")


blocktype = parser.add_mutually_exclusive_group()
blocktype.add_argument('--regex', action='store_true',
                       help='use regex blocking.')
blocktype.add_argument('--domain', action='store_true',
                       help='use hostfile blocking.')


parser.add_argument('--temporary', action='store_true',
                    help='apply temporary configurations to client, will be removed on service reboot.')

parser.add_argument('list', action='store_true',
                    help='list all connected clients.')


class MasterCLI:
    def __init__(self, port):
        passwd = input('Enter password:')
        ysecret.load_private_key(os.path.join(
            DEFAULT_KEY_LOCATION, DEFAULT_PRIVATE_KEY_FILE), password=passwd)

        if ysecret._private_key:  # was loaded, run CLI
            # configure socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3.0)
            setattr(self, 'sock', sock)

            # load client list
            self._load_clients()
            # start cli
            self._main_loop()

    def _main_loop(self):
        while True:
            try:
                x = input('>>')
                if x:
                    if x in ['help', '/?', '-h']:
                        parser.print_help()
                    elif x == 'exit':
                        raise KeyboardInterrupt()
                    else:
                        self.run_command(args=parser.parse_args(x.split(' ')))
            except KeyboardInterrupt:
                exit()
            except:
                pass

    def _load_clients(self):
        try:
            clients = {}
            with open(CLIENT_LIST, 'rb') as rec_file:
                clients = pickle.load(rec_file)
        except Exception as e:
            print(e)
        finally:
            setattr(self, 'clients', clients)

    def run_command(self, args):
        if args.block:
            print('block', args.block.split(','))
            print('target', args.target.split(','))
            return


cli = MasterCLI(4000)
