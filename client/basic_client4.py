from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import time
import socket 


HOST = '127.0.0.1'
PORT = 4090

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((HOST, PORT))


# private key
private_key = ec.generate_private_key(ec.SECP384R1, default_backend())

# public key
public_key = private_key.public_key()

# public key bytes to send
public_key_bytes = public_key.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)

# send public key
s.sendto(public_key_bytes, (HOST, 1337))

# get server's public key 
data, server_addr = s.recvfrom(1024)

# load server's public key
server_public_key = serialization.load_pem_public_key(data, backend=default_backend())

# perform exchange
shared_key = private_key.exchange(ec.ECDH(), server_public_key)

# compare shared keys
derived_key = HKDF(
    algorithm=hashes.SHA256(),
    length=32,
    salt=None,
    info=b'handshake data',
    backend=default_backend()
).derive(shared_key)

# encrypt/decrypt
aesgcm = AESGCM(derived_key)
mess = b'witaj serwerze!'
aad = b"authenticated but unencrypted data"

nonce = os.urandom(12)
ct = aesgcm.encrypt(nonce, mess, None)

time.sleep(3)
s.sendto(nonce + ct, server_addr)

data = s.recv(1024)

print(aesgcm.decrypt(data[:12], data[12:], None))

