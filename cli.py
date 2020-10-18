#!/usr/bin/env python3

import json
import sys
from argparse import ArgumentParser
import _jsonnet
import requests


def load_state(args):
    payload = json.loads(_jsonnet.evaluate_file(args.state_file))
    response = requests.post('%s/state' % args.striv_url, json=payload)
    if response.status_code != requests.codes['ok']:
        raise RuntimeError(response.text)
    print(response.json())


def parser(args):
    parser = ArgumentParser(description='striv utilities')
    parser.add_argument('--striv-url', help='http[s]://host[:port]')
    commands = parser.add_subparsers()
    load_state_cmd = commands.add_parser(
        'load_state',
        help='Load a jsonnet script as state'
    )
    load_state_cmd.add_argument('state_file')
    load_state_cmd.set_defaults(handler=load_state)
    return parser.parse_args(args)


if __name__ == '__main__':
    args = parser(sys.argv[1:])
    args.handler(args)
