import base64
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa


def deserialize_private_key(private_key_pem):
    return serialization.load_pem_private_key(
        private_key_pem.encode('utf-8'),
        password=None,
        backend=default_backend()
    )


def decrypt_value(private_key, encrypted):
    encrypted = json.loads(base64.b64decode(encrypted).decode('utf-8'))
    symmetric_key = private_key.decrypt(
        base64.b64decode(encrypted['key'].encode('utf-8')),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    cleartext = Fernet(symmetric_key).decrypt(
        encrypted['payload'].encode('ascii'))
    return cleartext.decode('utf-8')


def encrypt_value(public_key, cleartext):
    public_key = serialization.load_pem_public_key(
        public_key.encode('utf-8'),
        backend=default_backend()
    )
    symmetric_key = Fernet.generate_key()
    encrypted_key = public_key.encrypt(
        symmetric_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    payload = Fernet(symmetric_key).encrypt(cleartext.encode('utf-8'))
    encrypted = {
        'key': base64.b64encode(encrypted_key).decode('ascii'),
        'payload': payload.decode('ascii'),
    }
    return base64.b64encode(json.dumps(encrypted).encode('utf-8')).decode('ascii')


def generate_key():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    return pem.decode('ascii')


def recover_pubkey(private_key):
    pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return pem.decode('ascii')
