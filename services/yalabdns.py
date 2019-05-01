import threading
import time
from dnslib import RCODE, DNSRecord, DNSHeader, DNSQuestion, RR, A, server
from yaglobal import blacklist, DNS_PORT, DNS_FORWARDER, DNS_HOST, EVENT_APPLY_UPDATES, EVENT_STOP_DNS_SERVICE

# NOTE: blacklist is READONLY, blacklist updates MUST be handled in services/blacklistd thread


class LocalResolver:
    def resolve(self, request, handler):
        d = request.reply()
        q = request.get_q()
        q_name = str(q.qname)
        client_addr = handler.client_address[0]

        if blacklist.check(client_addr, q_name):
            d.header.rcode = RCODE.NXDOMAIN
            d.add_answer(RR(q_name, ttl=10, rdata=A('0.0.0.0')))
        else:
            a = DNSRecord.parse(DNSRecord.question(
                q_name).send(DNS_FORWARDER, DNS_PORT))
            for rr in a.rr:
                d.add_answer(rr)
        return d


def service():
    global blacklist_count
    blacklist_count = blacklist.count()
    resolver = LocalResolver()
    s = server.DNSServer(resolver, address=DNS_HOST, port=DNS_PORT)
    s.start_thread()
    print('started service yalabdns')
    while True:
        if threading.Event.is_set(EVENT_STOP_DNS_SERVICE):
            break
        if threading.Event.is_set(EVENT_APPLY_UPDATES):
            print('applying updates...')
            new_count = blacklist.count()
            print('previous', blacklist_count)
            print('after update', new_count)
            blacklist_count = new_count
            time.sleep(10)
        time.sleep(1)
    s.stop()
    print('stopped yalabdns service')


def Server():
    return threading.Thread(target=service, name='yalabdns', daemon=True)
