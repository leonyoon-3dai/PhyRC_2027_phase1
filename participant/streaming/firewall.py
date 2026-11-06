#!/usr/bin/env python3
"""Restrict PhyRC streaming ports in a dedicated native nftables table.

Only locally destined TCP 8210/8211/49100 and UDP 47998 are filtered. Other
firewall tables are untouched. The prerouting hook avoids NetBird's automatic
INPUT interface allow rules. An accept here does not override a later drop.
"""
import argparse
import ipaddress
import json
import shlex
import subprocess

TABLE = 'phyrc_stream'
TCP_PORTS = [8210, 8211, 49100]
UDP_PORT = 47998


def command(tool, *arguments, input_text=None):
    return subprocess.run(['sudo', '-n', tool, *arguments], input=input_text,
                          capture_output=True, text=True)


def ipv4(value):
    return str(ipaddress.IPv4Address(value))


def table_state():
    result = command('nft', '--json', 'list', 'table', 'inet', TABLE)
    if result.returncode:
        if 'No such file or directory' in result.stderr or 'command not found' in result.stderr:
            return None
        raise RuntimeError('Cannot inspect native nftables table; check sudo and nft availability')
    return json.loads(result.stdout)


def rules_script(client, relays, *, replace):
    client, relays = ipv4(client), sorted(set(map(ipv4, relays)))
    relay_rules = '\n'.join(f'    iifname "wt0" ip saddr {address} accept' for address in relays)
    prefix = f'delete table inet {TABLE}\n' if replace else ''
    return prefix + f'''table inet {TABLE} {{
  chain stream_acl {{
    iifname "lo" accept
    ip saddr {client} accept
{relay_rules}
    drop
  }}
  chain prerouting {{
    type filter hook prerouting priority -10; policy accept;
    fib daddr type local tcp dport {{ 8210, 8211, 49100 }} jump stream_acl
    fib daddr type local udp dport 47998 jump stream_acl
  }}
}}
'''


def match(left, right):
    return {'match': {'op': '==', 'left': left, 'right': right}}


def interface(name):
    return match({'meta': {'key': 'iifname'}}, name)


def source(address):
    return match({'payload': {'protocol': 'ip', 'field': 'saddr'}}, address)


def expected_rules(client, relays):
    acl = [[interface('lo'), {'accept': None}], [source(client), {'accept': None}]]
    acl.extend([interface('wt0'), source(address), {'accept': None}]
               for address in sorted(set(relays)))
    acl.append([{'drop': None}])
    return {
        'stream_acl': acl,
        'prerouting': [
            [match({'fib': {'result': 'type', 'flags': ['daddr']}}, 'local'),
             match({'payload': {'protocol': 'tcp', 'field': 'dport'}}, {'set': TCP_PORTS}),
             {'jump': {'target': 'stream_acl'}}],
            [match({'fib': {'result': 'type', 'flags': ['daddr']}}, 'local'),
             match({'payload': {'protocol': 'udp', 'field': 'dport'}}, UDP_PORT),
             {'jump': {'target': 'stream_acl'}}],
        ],
    }


def normalized(value):
    if isinstance(value, dict):
        return {key: sorted((normalized(item) for item in val), key=str) if key == 'set'
                else normalized(val) for key, val in value.items()}
    if isinstance(value, list):
        return [normalized(item) for item in value]
    return value


def extract_state(state):
    chains, rules, tables = {}, {}, []
    for item in state.get('nftables', []):
        if len(item) != 1:
            raise ValueError('Unexpected nft object')
        kind, value = next(iter(item.items()))
        if kind == 'metainfo':
            continue
        if kind not in ('table', 'chain', 'rule'):
            raise ValueError('Unexpected object in streaming table')
        if value.get('family') != 'inet':
            raise ValueError('Streaming firewall must use inet to cover IPv6')
        if kind == 'table':
            if {k: v for k, v in value.items() if k != 'handle'} != {'family': 'inet', 'name': TABLE}:
                raise ValueError('Unexpected or inactive streaming table')
            tables.append(value)
            continue
        if value.get('table') != TABLE:
            raise ValueError('Unexpected table reference')
        if kind == 'chain':
            name = value['name']
            if name in chains:
                raise ValueError('Duplicate chain')
            chains[name] = {k: v for k, v in value.items() if k not in ('handle', 'family', 'table')}
        else:
            rules.setdefault(value['chain'], []).append(value['expr'])
    if len(tables) != 1:
        raise ValueError('Exactly one streaming table required')
    expected_chains = {
        'stream_acl': {'name': 'stream_acl'},
        'prerouting': {'name': 'prerouting', 'type': 'filter', 'hook': 'prerouting', 'prio': -10, 'policy': 'accept'},
    }
    if chains != expected_chains:
        raise ValueError('Streaming chains or prerouting hook differ from the intended configuration')
    return rules


def verify(state, client, relays):
    if normalized(extract_state(state)) != normalized(expected_rules(ipv4(client), map(ipv4, relays))):
        raise ValueError('Installed streaming rules differ from the intended client/relay/port restrictions')


def verify_installed_native(state):
    """Infer addresses only, then verify every chain, rule and match exactly."""
    rules = extract_state(state)
    acl = rules.get('stream_acl', [])
    try:
        client = ipv4(acl[1][0]['match']['right'])
        relays = [ipv4(rule[1]['match']['right']) for rule in acl[2:-1]]
    except (IndexError, KeyError, TypeError, ValueError) as error:
        raise ValueError('Malformed installed streaming allowlist') from error
    verify(state, client, relays)


def verify_installed_legacy():
    """Read-only compatibility for the previous IPv4 iptables helper."""
    result = command('iptables', '-S', 'PHYRC_STREAM')
    if result.returncode:
        raise ValueError('No verified native table or legacy PHYRC_STREAM chain is installed')
    lines = [shlex.split(line) for line in result.stdout.splitlines() if line.startswith('-A ')]
    try:
        client = str(ipaddress.IPv4Network(lines[0][3], strict=True))
        if not client.endswith('/32'):
            raise ValueError('Client must be one IPv4 address')
    except (IndexError, ValueError) as error:
        raise ValueError('Malformed legacy streaming client rule') from error
    expected = [['-A','PHYRC_STREAM','-s',client,'-j','ACCEPT'],
                ['-A','PHYRC_STREAM','-s','127.0.0.1/32','-j','ACCEPT'],
                ['-A','PHYRC_STREAM','-j','DROP']]
    if lines != expected:
        raise ValueError('Legacy streaming rules are not the expected restricted allowlist')
    inputs = command('iptables', '-S', 'INPUT')
    if inputs.returncode:
        raise ValueError('Cannot verify legacy streaming input jumps')
    jumps = [shlex.split(line) for line in inputs.stdout.splitlines() if 'PHYRC_STREAM' in line]
    expected_jumps = [['-A','INPUT','-p','tcp','-m','multiport','--dports','49100,8210,8211','-j','PHYRC_STREAM'],
                      ['-A','INPUT','-p','udp','-m','udp','--dport','47998','-j','PHYRC_STREAM']]
    if sorted(jumps) != sorted(expected_jumps):
        raise ValueError('Legacy streaming input jumps differ from the expected port restrictions')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client-ip', type=ipv4)
    parser.add_argument('--relay-ip', type=ipv4, action='append', default=[],
                        help='Observed IPv4 gateway allowed only on interface wt0; repeatable')
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--check', action='store_true', help='Verify installed native rules against all supplied addresses')
    modes.add_argument('--check-installed', action='store_true', help='Verify installed native or previous legacy restrictions')
    modes.add_argument('--dry-run', action='store_true', help='Validate native nft transaction without applying it')
    args = parser.parse_args()
    if not args.check_installed and not args.client_ip:
        parser.error('--client-ip is required')
    if args.check_installed and (args.client_ip or args.relay_ip):
        parser.error('--check-installed infers the installed allowlist; use --check for supplied addresses')
    try:
        state = table_state()
        if args.check_installed:
            if state is None:
                verify_installed_legacy()
                print('Legacy IPv4 streaming restriction verified; IPv6 coverage is not established')
            else:
                verify_installed_native(state)
                print('Native IPv4/IPv6 streaming restriction verified')
        elif args.check:
            if state is None:
                raise ValueError('Native streaming table is not installed')
            verify(state, args.client_ip, args.relay_ip)
            print('Native streaming rules match the supplied client and relay addresses')
        else:
            script = rules_script(args.client_ip, args.relay_ip, replace=state is not None)
            checked = command('nft', '--check', '--file', '-', input_text=script)
            if checked.returncode:
                raise RuntimeError('nft syntax/kernel validation failed; no firewall changes applied: ' + checked.stderr.strip())
            if args.dry_run:
                print('Native nft transaction validated; no firewall changes applied')
                return
            # Delete/recreate only our table in one atomic nft transaction.
            applied = command('nft', '--file', '-', input_text=script)
            if applied.returncode:
                raise RuntimeError('Atomic native nft transaction failed: ' + applied.stderr.strip())
            verify(table_state(), args.client_ip, args.relay_ip)
            print('Native streaming restriction applied and verified; other firewall tables unchanged')
    except (RuntimeError, ValueError, OSError) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()
