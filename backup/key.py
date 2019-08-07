#
# yalab/bin/key.py
#
import os
import argparse
import ysecret
import re
from yconst import constant
try:
    import cPickle as pickle
except:
    import pickle

CONFIG_FILE = 'config.dat'
ABS_PATH =  os.path.join(os.path.dirname(__file__), CONFIG_FILE)

def _load_config_file():
    data = None
    with open(ABS_PATH, 'rb') as f:
        data = pickle.load(f)
    return data

def _update_config_file(data):
    with open(ABS_PATH, 'wb') as f:
        pickle.dump(data, f)

def _list_keys(path):
    if not os.path.exists(path):
        raise Exception('Invalid directory %s' % path)
    else:
        print('list of private keys in %s' % path)
        p = re.compile('^.*_private\.pem$')
        for file_name in os.listdir(path):
            if p.match(file_name):
                print('  %s' % file_name)

class _Const():
    @constant
    def secret():
        return ysecret

const = _Const()


# to configure key_path and key_file
if __name__ == '__main__':
    CONFIG = {
        'key_path':None,
        'key_file':None
    }
    if not os.path.exists(ABS_PATH):
        _update_config_file(CONFIG)
    else:
        CONFIG = _load_config_file()
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, help='RSA key basedir.')
    parser.add_argument('--file', type=str, help='RSA private_key filename.')
    parser.add_argument('--list', action='store_true', help='list all RSA private_key filename configured PATH.')
    parser.add_argument('--info', action='store_true', help='display current private key.')
    args = parser.parse_args()

    if args.path:
        CONFIG['key_path'] = args.path
        print('config.key_path changed to %s' % args.path)
    if args.file:
        CONFIG['key_file'] = args.file
        print('config.key_file changed to %s' % args.file)
    if args.list:
        _list_keys(CONFIG.get('key_path'))
    if args.info:
        print(os.path.join(CONFIG.get('key_path'), CONFIG.get('key_file')))

    _update_config_file(CONFIG)

# for CLI bin imports
else:
    config = _load_config_file() 
    PATH = config.get('key_path')
    FILE = config.get('key_file')
    if PATH and FILE:
        try:
            ysecret.load_private_key(os.path.join(PATH, FILE))
        except Exception as e:
            print('Warining: %s' % e)
            pass
    else:
        raise Exception('invalid key configuration. specify a valid key_path and key_file before running the command.')

