#!/usr/bin/env bash
# Rebuild participant host helpers and the unchanged official environment.
set -euo pipefail
umask 0002
cd "$(dirname "$0")/../.."
mode=${1:---check}
case "$mode" in --check|--install) ;; *) printf 'Usage: %s [--check|--install]\n' "$0" >&2; exit 2;; esac
for tool in git docker nvidia-smi python3 curl flock xauth uv; do
    command -v "$tool" >/dev/null || { printf 'Missing prerequisite: %s; see docs/competition/SETUP.md\n' "$tool" >&2; exit 1; }
done
docker info --format 'Docker {{.ServerVersion}}'
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv
if [[ "$mode" == --check ]]; then
    printf 'Host prerequisites available. GPU/Vulkan runtime requires the official smoke test.\n'
    exit 0
fi
if [[ ! -d .venv ]]; then uv venv --python 3.12 .venv; fi
uv pip install --python .venv/bin/python numpy==1.26.4 h5py==3.12.1 pillow==11.0.0 psutil==6.1.1
uv tool install huggingface_hub==2.2.0
session_id="$(date -u +%Y%m%dT%H%M%SZ)-bootstrap"
mkdir -p "output/sessions/$session_id"
./run.sh doctor > "output/sessions/$session_id/doctor.log" 2>&1
.venv/bin/python participant/ops/run.py --id "$session_id-build" -- ./run.sh build
.venv/bin/python participant/ops/run.py --id "$session_id-prepare" -- ./run.sh prepare
.venv/bin/python participant/ops/run.py --id "$session_id-smoke" --success-marker PHYRC-SMOKE-PASS -- ./run.sh smoke
