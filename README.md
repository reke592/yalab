#You Allow and Block
Sample website blocker using dnslib

#Target
To create a client-server to block website access for computer lab
Yalab Master - to update client qname blacklist
Yalab Client - installed in computers to resolve DNS queries. forward DNSRecord query iff qname is NOT in blacklist

Computer Network config for target computers where we need to control website access:
IP static or dynamic
DNS 127.0.0.1

Computer Network config for YalabMaster
IP static or dynamic
DNS any or auto

#Setup
create rsa key-pair using yalabsvc.py
run Yalab as Master:
yalabsvc.py --master --key private_key_file.pem --run

run Yalab as Client:
yalabsvc.py --key-import public_key_file.pem
yalabsvc.py --client --run
