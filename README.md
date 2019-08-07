# You Allow and Block
Sample Python website blocker using dnslib
By the mean time, we can test the DNS blocking by manually adding entries in allow.list or deny.list under services/data/intercept directory and rerun the yalabsvc.py --client.

# TODO
Create socket event to update contents of client data/intercept
Figure out how we send the commands. create WebUI or focus to terminal (CLI).
Need to study more about security.
Remove the feature HostFileInterceptor. RR redirects can be abused to create a cybercrime like phishing.

# MAJOR CHANGE in code design and transaction flow under branch dev.
Needs change:
- Use Queue instead of spawning thread workers per qname request
- Create some sort of gateway for socket events
- Implement a Pubsub pattern to easily connect multiple service in socket event gateway also to lessen the sourcefile cluttering.
- Try to implement Eliptic curve instead of regenerating the Fernet key per client socket response

# Target
To create a client-server to block website access for computer lab
Implement some sort of Directory Service Discovery Protocol using UDP multicast.
Yalab Master - to update client qname blacklist
Yalab Client - installed in computers to resolve DNS queries. forward DNSRecord query iff qname is NOT in blacklist

Computer Network config for target computers where we need to control website access:
IP static or dynamic
DNS 127.0.0.1

Computer Network config for YalabMaster
IP static or dynamic
DNS any or auto

# Setup
Run yalabsvc.py -h to show help.

```
python yalabsvc.py --key-generate sample
```
This command will create and RSA key-pair used for signature and encryption, key file can be located in ./services/keys
Note: the RSA private key is bounded to the computer and user where it was created.

```
python yalabsvc.py --key-import abs_path/to/key_file.pem
```
run the above command in computers where we want to run Yalab as client (the computers we want to block website access)
this command will copy the 'key_file.pem' to a fixed filename 'public_key.pem' under ./services/keys directory.

```
python yalabsvc.py --client --run
```
Run Yalab as Client. Note: this command will require sudo permission in Linux because we use the socket port 53.
Yalab Client will use the default gateway configuration iff the --forwarder option is not defined.
By the mean time, we can test the DNS blocking by manually adding entries in allow.list or deny.list under services/data/intercept directory.

```
python yalabsvc.py --client --forwarder 192.168.10.10 --run
```
Yalab Client will forward the allowed qname to the 192.168.10.10. make sure 192.168.10.10 can resolve DNS queries.

```
python yalabsvc.py --master --key sample --run
```
Run Yalab as Master. Notice we only use the prefix we used before not the absolute path.
