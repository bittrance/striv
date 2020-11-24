import re
import pytest
from striv import crypto


@pytest.fixture
def private_key():
    return crypto.deserialize_private_key(crypto.generate_key())


@pytest.fixture
def public_key(private_key):
    return crypto.recover_pubkey(private_key)


def test_encrypted_text_is_base64(public_key):
    cleartext = 'verrah-secret'
    encrypted = crypto.encrypt_value(public_key, cleartext)
    assert re.match('^[A-Za-z0-9+/]+={0,2}$', encrypted)


def test_roundtrip(private_key, public_key):
    cleartext = 'verrah-secret'
    encrypted = crypto.encrypt_value(public_key, cleartext)
    assert encrypted != cleartext
    decrypted = crypto.decrypt_value(private_key, encrypted)
    assert decrypted == cleartext


def test_roundtrip_with_large_payload(private_key, public_key):
    cleartext = 'text' * 10000
    encrypted = crypto.encrypt_value(public_key, cleartext)
    decrypted = crypto.decrypt_value(private_key, encrypted)
    assert decrypted == cleartext
