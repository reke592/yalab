# yalabdns.py
# author: Erric Rapsing
#
#    YALAB (You allow and Block) a DNS proxy to allow, block or redirect DNS query using interceptors.
#
#        + HostFileInterceptor, using a host file to resolve qname
#        + RegexInterceptor, using a list of hostnames to forward or block the request
#
#        - DomainInterceptor, will redirect the request to DC when qname matches the realm.
#
#    project status: Experimental
#

import argparse
import os
import re
import time

from dnslib import server, RCODE, RR, A, DNSRecord

DEFAULT_DNS_FORWARDER = '192.168.1.1'
DEFAULT_DNS_TIMEOUT = 10

parser = argparse.ArgumentParser()

parser.add_argument('--config', type=str,
                    help='configuration file path. if not exist will create new.')

parser.add_argument('-t', '--timeout', type=int, default=DEFAULT_DNS_TIMEOUT,
                    help='set DNS request timeout. default %ds.' % DEFAULT_DNS_TIMEOUT)

parser.add_argument('-f', '--forwarder', type=str, default=DEFAULT_DNS_FORWARDER,
                    help='set DNS Forwarder IP address. default %s.' % DEFAULT_DNS_FORWARDER)

parser.add_argument('--hostfile',
                    help='list of IP addresses with hostname.')

parser.add_argument('--regex-allow',
                    help='list of domain names. match results action forwarded.')

parser.add_argument('--regex-deny',
                    help='list of domain names. match results action blocked.')

parser.add_argument('--domain-realm',
                    help='domain realm, if the client network is domain network.')

parser.add_argument('--domain-controller',
                    help='domain controller IP address, required when using domain realm.')


# Interceptor
class Interceptor:
    # return:
    #   True = request intercepted
    #   False = request forwarded to next interceptor or forwarder
    # params:
    #   done: type=function, return=True, skip all interceptor for current request
    #   res: DNS reply
    def test(self, qname, res, done):
        raise Exception('not implemented')


class DomainInterceptor(Interceptor):
    def __init__(self, realm, address, timeout):
        setattr(self, 'dc', address)
        setattr(self, 'regex', re.compile('(^|.*\.)(%s)' % realm))
        setattr(self, 'timeout', timeout)

    def test(self, qname, res, done):
        if getattr(self, 'regex').match(qname):
            print('forwarded to dc', getattr(self, 'dc'))
            a = DNSRecord.parse(DNSRecord.question(qname).send(
                dest=getattr(self, 'dc'), port=53, timeout=getattr(self, 'timeout')))
            for rr in a.rr:
                res.add_answer(rr)
            return done()
        else:
            return False


class HostFileInterceptor(Interceptor):
    # Hostfile format
    # IP    HOSTNAME
    def __init__(self, file_path):
        hosts = {}
        with open(file_path, 'r') as f:
            for i in f.readlines():
                r = i.replace('\t', ' ').split(' ')
                resolv = r[0]
                name = r[-1] + '.'
                hosts[name] = resolv
        setattr(self, 'hosts', hosts)

    def test(self, qname, res, done):
        data = getattr(self, 'hosts').get(qname)
        if data:
            res.add_answer(RR(qname, ttl=60, rdata=A(data)))
            return done()
        else:
            return False


class RegexInterceptor(Interceptor):
    def __init__(self, file_path, block=True):
        hosts = {}
        with open(file_path, 'r') as f:
            # remove doubles
            for i in f.readlines():
                hosts[i.replace('\n', '')] = block

            # create pattern
            pattern = '(^|.*\.)({0})'.format('|'.join(hosts.keys()))

            # if the list of hosts is not empty
            if len(hosts):  # compile the regex
                setattr(self, 'regex', re.compile(pattern))
            else:  # set regex to None, the interceptor will do nothing
                setattr(self, 'regex', None)

            # set the blocking action to be perform on matched qname
            # True = block the request
            # False = pass the request to forwarder
            setattr(self, 'block', block)

    def test(self, qname, res, done):
        expr = getattr(self, 'regex')
        # if pattern is empty, do not intercept, proceed to next interceptor or forwarder address
        if not expr:
            return False

        # else: test the qname
        if expr.match(qname):
            if getattr(self, 'block'):
                res.header.rcode = RCODE.NXDOMAIN
                # res.add_answer(RR(qname, ttl=60, rdata=A('0.0.0.0')))
                # skip the remaining interceptors
                # we return done() because we intercept the response
                return done()  # = True
            else:
                # skip the remaining interceptors
                # return false, because we  want to forward the request to forwarder address (whitelist)
                done()
                return False


class Proxy:
    def __init__(self, interceptors: Interceptor = []):
        setattr(self, 'interceptors', interceptors)

    def done(self):
        setattr(self, 'skip', True)
        return True

    def intercept(self, qname, res):
        setattr(self, 'skip', False)
        result = False
        try:
            for i in getattr(self, 'interceptors'):
                if i.test(qname, res, self.done):
                    result = True
                if getattr(self, 'skip'):  # skip the remaining interceptor
                    break
        except Exception as e:
            print(e)
        finally:
            # setattr(self, 'skip', False)  # for next query, do not skip
            return result


class Resolver:
    def __init__(self, proxy: Proxy, args):
        setattr(self, 'proxy', proxy)
        setattr(self, 'args', args)

    def resolve(self, request, handler):
        d = request.reply()
        q = request.get_q()
        q_name = str(q.qname)
        client_addr = handler.client_address[0]

        if getattr(self, 'proxy').intercept(q_name, d):
            return d
        else:
            args = getattr(self, 'args')
            a = DNSRecord.parse(DNSRecord.question(q_name).send(
                args.forwarder, 53, timeout=args.timeout))
            for rr in a.rr:
                d.add_answer(rr)
            return d


def configure(config_file, var):
    if not os.path.exists(config_file):
        # write configuration file
        with open(config_file, 'w') as f:
            for k in var.keys():
                if not k == 'config':
                    f.write('{}={}\n'.format(k, var[k] or ''))
    try:
        # read configuration file
        config_args = []
        with open(config_file, 'r') as f:
            for i in f.readlines():
                opt, val = i.strip('\n').split('=')
                # use options with defined value in config_file
                if val:
                    opt = opt.replace('_', '-')
                    config_args.extend(['--' + opt, val])

    except Exception as e:
        print('Something went wrong when reading configuration file', config_file)
        print('Error {0}: {1}.'.format(type(e), e))

    finally:
        # update service args
        return parser.parse_args(config_args)


def serve():
    args = parser.parse_args()

    interceptors = []

    # read configuration file
    if args.config:
        var = vars(args)
        args = configure(args.config, var)

    # EXPERIMENTAL
    # use DomainInterceptor, all qname that matches domain-realm pattern will be forwarded to DC
    if args.domain_realm:
        if not args.domain_controller:
            raise Exception('specify domain controller address')
        else:
            interceptors.append(DomainInterceptor(
                args.domain_realm, args.domain_controller, args.timeout))

    # use HostFileInterceptor
    if args.hostfile:
        interceptors.append(HostFileInterceptor(args.hostfile))

    # use RegexInterceptor, matched qname will be forwarded (whitelist)
    if args.regex_allow:
        interceptors.append(RegexInterceptor(args.regex_allow, block=False))

    # use RegexInterceptor, matched qname will be forwarded (blacklist)
    if args.regex_deny:
        interceptors.append(RegexInterceptor(args.regex_deny, block=True))

    resolver = Resolver(Proxy(interceptors), args)
    s = server.DNSServer(resolver, address='127.0.0.1', port=53)
    s.start_thread()
    while True:
        time.sleep(1)


if __name__ == '__main__':
    serve()
