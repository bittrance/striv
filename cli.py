#!/usr/bin/env python3

import json
import sys
from argparse import ArgumentParser
import _jsonnet
import requests

from striv import crypto


def decrypt_value(args):
    if args.encrypted.startswith('{'):
        secret_value = json.loads(args.encrypted)
        if secret_value.get('type') != 'secret':
            raise RuntimeError('Encrypted is JSON object but not type=secret')
        encoded = secret_value['encrypted'].encode('utf-8')
    else:
        encoded = args.encrypted.encode('utf-8')
    return crypto.decrypt_value(args.private_key, encoded)


def encrypt_value(args):
    return json.dumps({
        '_striv_type': 'secret',
        'encrypted': crypto.encrypt_value(
            args.public_key,
            args.cleartext
        )
    })


def generate_key(args):
    return crypto.generate_key()


def load_state(args):
    payload = json.loads(_jsonnet.evaluate_file(args.state_file))
    response = requests.post('%s/state' % args.striv_url, json=payload)
    if response.status_code != requests.codes['ok']:
        raise RuntimeError(response.text)
    return response.json()


def recover_pubkey(args):
    return crypto.recover_pubkey(args.private_key)


def parser(args):
    parser = ArgumentParser(description='striv utilities')
    parser.add_argument('--striv-url', help='http[s]://host[:port]')
    commands = parser.add_subparsers()
    decrypt_cmd = commands.add_parser(
        'decrypt-value',
        help='Encrypts a secret and outputs a json(net) value'
    )
    decrypt_cmd.add_argument('--private-key', help='Private key PEM string')
    decrypt_cmd.add_argument('encrypted')
    decrypt_cmd.set_defaults(
        handler=lambda args: print(decrypt_value(args))
    )
    encrypt_cmd = commands.add_parser(
        'encrypt-value',
        help='Encrypts a secret and outputs a json(net) value'
    )
    encrypt_cmd.add_argument('--public-key', help='Public key PEM string')
    encrypt_cmd.add_argument('cleartext')
    encrypt_cmd.set_defaults(
        handler=lambda args: print(encrypt_value(args))
    )
    generate_key_cmd = commands.add_parser(
        'generate-key',
        help='Generate a new crypto key for managing secrets'
    )
    generate_key_cmd.set_defaults(
        handler=lambda args: print(generate_key(args))
    )
    load_state_cmd = commands.add_parser(
        'load-state',
        help='Load a jsonnet script as state'
    )
    load_state_cmd.add_argument('state_file')
    load_state_cmd.set_defaults(
        handler=lambda args: print(load_state(args))
    )
    recover_pubkey_cmd = commands.add_parser(
        'recover-public-key',
        help='Calculates the public key from a private key'
    )
    recover_pubkey_cmd.add_argument('--private-key', help='Private key PEM')
    recover_pubkey_cmd.set_defaults(
        handler=lambda args: print(recover_pubkey(args))
    )

    return parser.parse_args(args)


if __name__ == '__main__':
    args = parser(sys.argv[1:])
    args.handler(args)
