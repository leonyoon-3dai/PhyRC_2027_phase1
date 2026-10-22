#!/usr/bin/env python3
"""Scaffold NVIDIA's pinned viewer locally; apply participant keyboard bridge.

NVIDIA-generated viewer stays in ignored output/, with its supplied license.
"""
import os
from pathlib import Path
import shutil
import subprocess
ROOT=Path(__file__).resolve().parents[2]
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
if "import './phyrc-keyboard.js';" not in s:
    expected="signalingServer: '127.0.0.1',"
    if expected not in s:raise RuntimeError('unexpected viewer source; inspect scaffold revision')
    s="import './phyrc-keyboard.js';\n"+s.replace(expected,"signalingServer: window.location.hostname,\n            signalingPort: 49100,\n            mediaServer: window.location.hostname,\n            mediaPort: 47998,\n            forceWSS: false,")
    entry.write_text(s)
shutil.copyfile(ROOT/'participant/streaming/keyboard.js',viewer/'src/phyrc-keyboard.js')
lock=ROOT/'participant/streaming/viewer-package-lock.json'
if lock.exists():
    shutil.copyfile(lock,viewer/'package-lock.json')
    subprocess.run(['npm','ci','--ignore-scripts'],cwd=viewer,env=env,check=True)
else:
    subprocess.run(['npm','install','--ignore-scripts'],cwd=viewer,env=env,check=True)
subprocess.run(['npm','run','build'],cwd=viewer,env=env,check=True)
print('Viewer built; serve output/webrtc/viewer/dist on restricted port 8210')
