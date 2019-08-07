from dnslib import server, RCODE, RR, A, DNSRecord
import time

class Resolver(object):
    def resolve(self, req, handl):
        d = req.reply()
        q = req.get_q()
        qname = str(q.qname)

        print(qname)
        forwarded = DNSRecord.question(qname).send('', timeout=3)
        for rr in DNSRecord.parse(forwarded).rr:
            d.add_answer(rr)

        return d

dns = server.DNSServer(Resolver(), address='127.0.0.1', port=53)
dns.start_thread()

while True:
    time.sleep(1)

