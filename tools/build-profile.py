#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Build an MVSA voice profile from graph and command payloads."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

KINDS = {'GRAPH_OPEN': 1, 'SET_CFG': 2, 'REGISTER_CFG': 3, 'GRAPH_PREPARE': 4, 'GRAPH_START': 5}


def payload(entry):
    data = bytes.fromhex(entry['data'])
    if hashlib.sha256(data).hexdigest() != entry['sha256']:
        raise ValueError('payload SHA-256 mismatch')
    if len(data) % 8:
        raise ValueError('payload must be aligned to eight bytes')
    return data


def build(profile):
    if profile['format'] != 'q6apm-voice-profile-v1' or len(profile['graphs']) != 2:
        raise ValueError('unsupported profile format or graph count')
    graphs = [payload(graph) for graph in profile['graphs']]
    if not all(graphs) or sum(map(len, graphs)) + 16 > 65536:
        raise ValueError('invalid graph payload size')
    opened = struct.pack('<4I', 0x504f564d, 1, *map(len, graphs)) + b''.join(graphs)
    commands = profile['commands']
    if not 1 <= len(commands) <= 32:
        raise ValueError('invalid command count')
    result = bytearray(struct.pack('<4I', 0x4153564d, 1, len(opened), len(commands)) + opened)
    previous = 0
    for command in commands:
        kind = KINDS[command['type']]
        graph, destination, sequence = command['graph'], command['destination'], command['sequence']
        data = payload(command)
        if graph not in (0, 1) or not 0 < destination <= 0xffffffff or not previous < sequence <= 0xffffffff:
            raise ValueError('invalid command graph, destination or sequence')
        if kind in (1, 4, 5) and (data or destination != 1):
            raise ValueError('invalid graph lifecycle command')
        if kind in (2, 3) and not data:
            raise ValueError('empty configuration payload')
        result += struct.pack('<6I', kind, graph, destination, len(data), sequence, 0) + data
        previous = sequence
    if len(result) > 262144 or hashlib.sha256(result).hexdigest() != profile['binary_sha256']:
        raise ValueError('binary size or SHA-256 mismatch')
    return bytes(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('profile', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--check', action='store_true', help='compare with the existing binary without writing')
    args = parser.parse_args()
    try:
        data = build(json.loads(args.profile.read_text()))
        if args.check:
            if args.output.read_bytes() != data:
                raise ValueError('existing binary differs from profile')
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_bytes(data)
    except (OSError, ValueError, KeyError, TypeError, struct.error) as error:
        parser.exit(1, f'{parser.prog}: {error}\n')
    print(f'{args.output}: {len(data)} bytes, SHA-256 {hashlib.sha256(data).hexdigest()}')


if __name__ == '__main__':
    main()
