#!/usr/bin/env python3
"""Scaffold NVIDIA's pinned viewer locally; apply participant keyboard bridge.

NVIDIA-generated viewer stays in ignored output/, with its supplied license.
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--skip-install',action='store_true',help='Use already installed pinned dependencies')
parser.add_argument('--out-dir',default='dist',help='Build directory under the generated viewer; use dist-spectator for preview')
args=parser.parse_args()
base=ROOT/'output/webrtc'
base.mkdir(parents=True,exist_ok=True)
config=base/'npmrc'
config.write_text('@nvidia:registry=https://edge.urm.nvidia.com/artifactory/api/npm/omniverse-client-npm/\n')
env=dict(os.environ,NPM_CONFIG_USERCONFIG=str(config))
viewer=base/'viewer'
if not viewer.exists():
    subprocess.run(['npm','exec','--yes','--package=@nvidia/create-ov-web-rtc-app@1.14.2','--',
        'create-ov-web-rtc-app','--name','viewer','--sample','local-sample','--outputDir',str(base)],env=env,check=True)
entry=viewer/'src/main.ts'
s=entry.read_text()
s=s.replace("import './phyrc-keyboard.js';\n",'')
if "import './phyrc-spectator.js';" not in s:
    expected="signalingServer: '127.0.0.1',"
    if expected not in s and 'signalingServer: window.location.hostname,' not in s:
        raise RuntimeError('unexpected viewer source; inspect scaffold revision')
    s="import './phyrc-spectator.js';\n"+s.replace(expected,"signalingServer: window.location.hostname,\n            signalingPort: Number(new URLSearchParams(window.location.search).get('signalPort') || 49100),\n            mediaServer: window.location.hostname,\n            mediaPort: Number(new URLSearchParams(window.location.search).get('mediaPort') || 47998),\n            forceWSS: false,")
if 'phyrc-stream-state' not in s:
    s=s.replace('this.streamConnected = true;', "this.streamConnected = true;\n                        window.dispatchEvent(new CustomEvent('phyrc-stream-state', {detail: {sdk_connected: true}}));")
    s=s.replace('this.streamConnected = false;', "this.streamConnected = false;\n                window.dispatchEvent(new CustomEvent('phyrc-stream-state', {detail: {sdk_connected: false}}));")
    s=s.replace('this.state.streamFailed = true;', "this.state.streamFailed = true;\n                        window.dispatchEvent(new CustomEvent('phyrc-stream-state', {detail: {sdk_connected: false}}));")
s=s.replace("`${message.info || 'Unknown error'}`", "'영상 연결을 확인하고 있습니다.'")
s=s.replace("`${error || 'Unknown error'}`", "'영상 연결을 확인하고 있습니다.'")
# Apply the mapping to an existing previously generated viewer as well.
s=s.replace('signalingPort: 49100,', 'signalingPort: Number(new URLSearchParams(window.location.search).get("signalPort") || 49100),')
s=s.replace('mediaPort: 47998,', 'mediaPort: Number(new URLSearchParams(window.location.search).get("mediaPort") || 47998),')
entry.write_text(s)
shutil.copyfile(ROOT/'participant/streaming/spectator.js',viewer/'src/phyrc-spectator.js')
index=viewer/'index.html'
index.write_text(index.read_text().replace('lang="en"','lang="ko"').replace('<title>viewer</title>','<title>PhyRC 라이브 관찰</title>'))
lock=ROOT/'participant/streaming/viewer-package-lock.json'
if args.skip_install:
    if not (viewer/'node_modules').is_dir():raise RuntimeError('Dependencies are not installed')
elif lock.exists():
    shutil.copyfile(lock,viewer/'package-lock.json')
    subprocess.run(['npm','ci','--ignore-scripts'],cwd=viewer,env=env,check=True)
else:
    subprocess.run(['npm','install','--ignore-scripts'],cwd=viewer,env=env,check=True)
out=(viewer/args.out_dir).resolve()
if not out.is_relative_to(viewer.resolve()) or out==viewer.resolve():raise ValueError('Build output must be below the viewer directory')
subprocess.run(['npm','run','build','--','--outDir',str(out)],cwd=viewer,env=env,check=True)
print('Spectator viewer built; serve the selected build with participant.streaming.viewer_server on existing port 8210')
