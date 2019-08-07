#
# ~/yalab/services/ysecret.py
#
# TODO:
# 1: make the private key usable only by the current user and system it was created
#
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa, padding, utils
from cryptography.hazmat.primitives import serialization, hashes
import getpass
import os
import platform
import uuid

DEFAULT_ALGORITHM = hashes.SHA256()

def _sys_info():
    return ';'.join([hex(uuid.getnode()), platform.system(), getpass.getuser()])


def create_keys(directory=os.path.dirname(__file__), name: str = ''):
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    # 1
    encrypt_algo = serialization.BestAvailableEncryption(bytes(_sys_info(), 'utf-8'))
    public_key = private_key.public_key()

    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=encrypt_algo
    )
    # write private key file
    file_name = name + '_private.pem'
    with open(os.path.join(directory, file_name), 'wb') as f:
        f.write(pem)

    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    # write public key file
    file_name = name + '_public.pem'
    with open(os.path.join(directory, file_name), 'wb') as f:
        f.write(pem)


def load_public_key(file_path: str):
    try:
        public_key = None
        if not os.path.exists(file_path):
            raise FileNotFoundError('file not found %s' % file_path)
        else:
            with open(file_path, 'rb') as key_file:
                public_key = serialization.load_pem_public_key(
                    data=key_file.read(),
                    backend=default_backend()
                )
    except FileNotFoundError as e:
        raise e
    except Exception as e:
        raise Exception('Unable to load public key.')
    finally:
        global _public_key
        _public_key = public_key


def load_private_key(file_path: str):
    try:
        private_key = None
        if not os.path.exists(file_path):
            raise ValueError('file not found %s' % file_path)
        else:
            with open(file_path, 'rb') as key_file:
                private_key = serialization.load_pem_private_key(
                    data=key_file.read(),
                    password = bytes(_sys_info(), 'utf_8'), # 1
                    backend=default_backend()
                )
    except Exception as e:
        if 'Password was given' in str(e):  # just say invalid password
            raise Exception('invalid password.')
        else:
            raise e
    finally:
        global _private_key
        _private_key = private_key


def sign(data, prehashed=True):
    global _private_key
    if not _private_key:
        raise ValueError('Private key not loaded.')
    sig = None
    message = bytes(data, 'utf-8') if not type(data) is bytes else data
    if prehashed:  # for large data
        hasher = hashes.Hash(DEFAULT_ALGORITHM, default_backend())
        c = 0
        n = len(data)
        lim = 255
        while(c < n):
            hasher.update(message[c:lim])
            c = c + lim + 1
        digest = hasher.finalize()
        sig = _private_key.sign(
            data=digest,
            padding=padding.PSS(
                mgf=padding.MGF1(DEFAULT_ALGORITHM),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            algorithm=utils.Prehashed(DEFAULT_ALGORITHM)
        )
    else:
        sig = _private_key.sign(
            data=message,
            padding=padding.PSS(
                mgf=padding.MGF1(DEFAULT_ALGORITHM),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            algorithm=DEFAULT_ALGORITHM
        )
    return sig


def verify(data, sig, prehashed=True, enc='utf-8'):
    global _public_key
    if not _public_key:
        raise ValueError('Public key not loaded.')
    if not sig:
        raise ValueError('unable to verify message, missing signature.')

    message = bytes(data, enc) if type(data) is not bytes else data

    _padding = padding.PSS(
        mgf=padding.MGF1(DEFAULT_ALGORITHM),
        salt_length=padding.PSS.MAX_LENGTH
    )

    if prehashed:
        hasher = hashes.Hash(DEFAULT_ALGORITHM, default_backend())
        c = 0
        n = len(message)
        lim = 255
        while(c < n):
            hasher.update(message[c:lim])
            c = c + lim + 1
        digest = hasher.finalize()
        _public_key.verify(
            signature=sig,
            data=digest,
            padding=_padding,
            algorithm=utils.Prehashed(DEFAULT_ALGORITHM)
        )
    else:
        _public_key.verify(
            signature=sig,
            data=message,
            padding=_padding,
            algorithm=DEFAULT_ALGORITHM
        )


def encrypt(msg, enc='utf-8'):
    global _public_key
    if not _public_key:
        raise ValueError('Public key not loaded.')
    payload = bytes(str(msg), enc) if type(msg) is not bytes else msg
    ciphertext = _public_key.encrypt(
        payload,
        padding=padding.OAEP(
            mgf=padding.MGF1(algorithm=DEFAULT_ALGORITHM),
            algorithm=DEFAULT_ALGORITHM,
            label=None
        )
    )
    return ciphertext


def decrypt(ciphertext):
    global _private_key
    if not _private_key:
        raise ValueError('Private key not loaded.')
    plaintext = _private_key.decrypt(
        ciphertext,
        padding=padding.OAEP(
            mgf=padding.MGF1(algorithm=DEFAULT_ALGORITHM),
            algorithm=DEFAULT_ALGORITHM,
            label=None
        )
    )
    return plaintext

