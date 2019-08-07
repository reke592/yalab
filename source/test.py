#
# test.py
#
import secret
import struct
import socket
import cryptography as f
import eventgw
from cryptography.fernet import Fernet

key = b'8aZK6fmiDiuq-3kH-xna_SRJ2ciaYFNZuvM4sxDqg2E='

secret.load_private_key('keys/sample_private.pem')

event = eventgw.events.HANDSHAKE
test = (event, b'1234')
payload = eventgw.pack_payload(test[0], test[1])
payload = Fernet(key).encrypt(payload)
sig = secret.sign(payload)
data = eventgw.pack(payload, sig) 
SERV_ADDR = ('', 10011)
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.settimeout(0.3)
    s.connect(SERV_ADDR)
    s.send(data)
    while True:
        try:
            data = s.recv(1024)
            hstat, enc_payload, enc_key = eventgw.unpack(data)
            key = secret.decrypt(enc_key)
            payload = Fernet(key).decrypt(enc_payload)
            event, data = eventgw.unpack_payload(payload)
            print(event, data)
        except socket.timeout:
            print('no more response')
            break
        except Exception as e:
            print(e)
            break


    


#secret.load_public_key('keys/public_key.pem')
#secret.load_private_key('keys/sample_private.pem')
#sym_key = Fernet.generate_key()
#sym_key2 = Fernet.generate_key()
#secret = Fernet(sym_key2).encrypt(b'testing')
#print(sym_key)
#print(sym_key2)
#trans = b'' 
#for i in range(len(sym_key)):
#    xor = sym_key[i] ^ sym_key2[i]
#    trans = trans + xor.to_bytes(1, byteorder='big')
#    print("%3d %3d %3d %3d" % (sym_key[i], sym_key2[i], xor, sym_key[i] ^ xor))
#print(trans)

#enc_key = secret.encrypt(sym_key)
#fmt = '>?1H%ds256s'
#event_id = 65 
#message = b'test'
#print(len(sym_key))
#print(len(enc_key))
#
#data = b'1' + event_id.to_bytes(2, byteorder='big') + message + enc_key
#print(len(data) - len(message))
#unpacked = struct.unpack(fmt % len(message), data)
#print(data)
#print(unpacked)
#print(secret.decrypt(unpacked[3]) == sym_key)
