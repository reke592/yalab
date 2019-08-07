# 
# yalab/bin/config.py
#
# this module can:
#   list client configuration (the active blacklist, whitelist, and hostfile)
#   update client interceptors configuration
#
# Usage:
#   config TARGET [-a | --allow] pattern1,pattern2
#   config TARGET [-b | --block] pattern1,pattern2
#   config TARGET [-r | --redirect] hostname@IP_ADDR
#
# Where:
#   TARGET = client IDs separated by ',' (eg. 1,2,3)
#     to show client IDs run the command 'list [-c | --clients]'
#
import argparse
import os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('targets', type=str, help='target client IDs. (eg. 1,2,3).')
    parser.add_argument('-b','--block', type=str, help='block DNS qname pattern on target clients. (eg. abc.xyz,abc)')
    parser.add_argument('-a','--allow', type=str, help='allow DNS qname pattern, whitelist all qname that matches the pattern. (eg. abc.xyz,abc)')
    parser.add_argument('-r','--redirect', type=str, help='add entry to hostfile on target clients. (eg. abc.xyz@192.168.1.10')
    args = parser.parse_args()

    TARGETS = args.targets.split(',')

    for target in TARGETS:
        try:
            context = None
            print('config client %s' % target)
            if args.allow:
                context = 'allow'
                patterns = args.allow.split(',')
                for pattern in patterns:
                    print('  allow pattern %s' % pattern)
            if args.block:
                context = 'block'
                patterns = args.block.split(',')
                for pattern in patterns:
                    print('  block pattern %s' % pattern)
            if args.redirect:
                context = 'redirect'
                hostname, resolv = args.redirect.split('@')
                print('  update hostfile. add %s %s' % (resolv, hostname))
        except Exception as e:
            print('  Error: %s on %s argv' % (e, context))

if __name__ == '__main__':
    main()

