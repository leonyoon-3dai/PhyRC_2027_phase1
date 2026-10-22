#!/usr/bin/env python3
"""Restrict only PhyRC host-network streaming ports to one client IPv4 + loopback."""
import argparse
import ipaddress
import subprocess
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--client-ip',required=True)
p.add_argument('--check',action='store_true')
a=p.parse_args()
client=str(ipaddress.IPv4Address(a.client_ip))
base=['sudo','-n','iptables']
def run(*args,check=True):return subprocess.run([*base,*args],check=check,capture_output=True,text=True)
if a.check:
    value=run('-S','PHYRC_STREAM').stdout
    if f'-s {client}/32 -j ACCEPT' not in value or '-j DROP' not in value:raise SystemExit('client/drop restriction missing')
else:
    run('-N','PHYRC_STREAM',check=False)
    run('-F','PHYRC_STREAM')
    run('-A','PHYRC_STREAM','-s',client+'/32','-j','ACCEPT')
    run('-A','PHYRC_STREAM','-s','127.0.0.1/32','-j','ACCEPT')
    run('-A','PHYRC_STREAM','-j','DROP')
for rule in (['-p','tcp','-m','multiport','--dports','49100,8210,8211','-j','PHYRC_STREAM'],
             ['-p','udp','--dport','47998','-j','PHYRC_STREAM']):
    if run('-C','INPUT',*rule,check=False).returncode:
        if a.check:raise SystemExit('streaming port jump missing')
        run('-I','INPUT','1',*rule)
print('PhyRC IPv4 streaming restriction verified; no other ports changed')
