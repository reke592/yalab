# yalabdns.py
# author: Erric Rapsing
#
#    YALAB (You allow and Block) DNS proxy to allow, block DNS query.
#
#        + HostFileInterceptor, using a host file to resolve qname
#        + RegexInterceptor, using a list of hostnames to forward or block the request
#
#        - DomainInterceptor, will redirect the request to DC when qname matches the realm.
#
#    project status: Experimental
#
# TODO: create reload logic for interceptors
#
import atexit
import argparse
import os
import re
import time
import logging
import threading
import socket
import sys
import subprocess
import platform
from yconst import defaults as _Y
from dnslib import server, RCODE, RR, A, DNSRecord
try:
    import cPickle as pickle
except:
    import pickle


formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')
        
def setup_logger(name, log_file=None):
    global logger
    logger = logging.getLogger(name)
    if log_file:
        handler = logging.FileHandler(log_file)
        handler.setFormatter(formatter)
        logger.addHandler(handler)


def get_default_gw():
    logger.debug('find default gateway.')
    system = platform.system()
    try:
        ip_pattern = r'(?:\d{1,3}\.){3}(\d{1,3})'
        if system == 'Windows':
            out = subprocess.check_output(['ipconfig']).decode('utf_8')
            gw_str = re.search(r'(default.*:)(.*)', out.lower()).group()
            #gw = gw.group(2).strip() if gw is not None else ''
        elif system == 'Linux':
            out = subprocess.check_output(['ip', 'route']).decode('utf_8')
            gw_str = out
        else:
            raise Exception('%s platform is not yet supported by yalabdns.get_default_gw. Please specify the forwarder using "--forwarder=x.x.x.x" option.' % system)
    except Exception as e:
        logger.error(e)
        return None
    else:
        ip = re.search(ip_pattern, gw_str)
        return ip.group() if ip else None

setup_logger('YalabDNS')

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
    def __init__(self, realm: str, address: str, timeout: int):
        setattr(self, 'dc', address)
        setattr(self, 'regex', re.compile('(^|.*\.)(%s)' % realm))
        setattr(self, 'timeout', timeout)

    def test(self, qname, res, done):
        if getattr(self, 'regex').match(qname):
            logger.debug('DNS query forwarded to dc %s' % getattr(self, 'dc'))
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
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                pass
        self.hosts = {}
        with open(file_path, 'r') as f:
            for i in f.readlines():
                r = i.replace('\t', ' ').split(' ')
                resolv = r[0]  # ipaddr
                name = r[-1].strip() + '.'  # sub.dom.
                self.hosts[name] = resolv
        logger.info('Hostfile records: %d' % len(self.hosts.keys()))

    def test(self, qname, res, done):
        data = self.hosts.get(qname)
        if data:
            res.add_answer(RR(qname, ttl=60, rdata=A(data)))
            return done()
        else:
            return False


class RegexInterceptor(Interceptor):
    def __init__(self, file_path, block=True):
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                pass
        hosts = {}
        with open(file_path, 'r') as f:
            # remove doubles
            for entry in f.readlines():
                if len(entry) - 1:
                    hosts[entry.replace('\n', '')] = block

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
        logger.info('Regex %s patterns: %d' % ('blocked' if block else 'allowed', len(hosts.keys())))

    def test(self, qname, res, done):
        expr = getattr(self, 'regex')
        # if pattern is empty, do not intercept, proceed to next interceptor or forwarder address
        if not expr:
            return False

        # else: test the qname
        if expr.match(qname):
            if getattr(self, 'block'):
                res.header.rcode = RCODE.NXDOMAIN
                res.add_answer(RR(qname, ttl=60, rdata=A('0.0.0.0')))
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
            logger.debug(e)
        finally:
            # setattr(self, 'skip', False)  # for next query, do not skip
            return result


class Resolver:
    def __init__(self, proxy: Proxy, forwarder: str, timeout: int):
        setattr(self, 'timeout', timeout)
        self.timeout = timeout
        self.proxy = proxy
        self.forwarder = forwarder
        self.rcache = {}

    def resolve(self, request, handler):
        d = request.reply()
        q = request.get_q()
        q_name = str(q.qname)
        # resolve q_name 
        cached = self.rcache.get(q_name)
        # skip intercept / forward
        if cached:
            logger.info('Cached: %s' % q_name)
            cached = DNSRecord.parse(cached)
            for rr in cached.rr:
                d.add_answer(rr)
            d.header.rcode = cached.header.rcode
        # run interceptors, update reply then cache
        elif self.proxy.intercept(q_name, d) if self.proxy else False:
            self.rcache.setdefault(q_name, d.pack())
        # forward request, update reply then cache
        else:
            forwarded = DNSRecord.question(q_name).send(self.forwarder, timeout=self.timeout)
            for rr in DNSRecord.parse(forwarded).rr:
                d.add_answer(rr)
            self.rcache.setdefault(q_name, d.pack())
        # finally the DNSRecord.reply
        return d


# TODO: convert def main() to class
class Server(threading.Thread):
    def __init__(self, address='127.0.0.1', forwarder=None, port=53, timeout=3):
        super(Server, self).__init__()
        self.alive = threading.Event()
        self.lock = threading.Lock()
        self.alive.set()
        self.interceptors = []
        self.resolver = None
        self.proxy = None
        self.dns_server = None
        self.address = address
        self.port = port
        self.forwarder = forwarder
        self.timeout = timeout

    def add_interceptor(self, interceptor: Interceptor, priority=None):
        if not issubclass(type(interceptor), Interceptor):
            raise Exception('instance must be a subclass of Interceptor')
        last = len(self.interceptors) 
        self.interceptors.insert(priority if type(priority) is int else last, interceptor)

    def try_get_network_gw(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                dummy = (_Y.MULTICAST_GROUP, _Y.UDP_PORT)
                s.connect(dummy)
                IP = s.getsockname()[0]
                print(IP)
        except Exception as e:
            logger.debug(e)
            return None
        else:
            # Windows will return the loopback if not connected to network
            if IP == '127.0.0.1':
                return None
            else:
                MY_NETWORK = IP.split('.')[:-1]
                return '.'.join(MY_NETWORK) + '.1'

    def run(self):
        self.proxy = Proxy(self.interceptors)
        if not self.forwarder:
            logger.info('No configured forwarder. try get default gateway.')
            self.forwarder = get_default_gw()
        if not self.forwarder:
            logger.info('Waiting for network connection, will assume that network node in .1 is a gateway interface.')
            # hold self.dns_server
            while not self.forwarder and self.alive.is_set():
                self.forwarder = self.try_get_network_gw()
                if not self.forwarder:
                    time.sleep(2)
        self.resolver = Resolver(self.proxy, self.forwarder, self.timeout)
        self.dns_server = server.DNSServer(self.resolver, address=self.address, port=self.port)
        self.dns_server.start_thread()
        if self.dns_server.isAlive() and self.alive.is_set():
            logger.info('DNS Server running. forwarder: %s' % self.forwarder)
        while self.alive.is_set():
            # watch for Threading events here..
            time.sleep(1)

    def join(self, timeout=None):
        self.alive.clear()
        threading.Thread.join(self, timeout)
        if not self.dns_server.isAlive():
            logger.info('DNS Server stopped')
        if not self.is_alive():
            logger.info('YalabDNS thread stopped')
