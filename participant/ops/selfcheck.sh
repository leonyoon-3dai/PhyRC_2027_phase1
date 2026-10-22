#!/usr/bin/env bash
# Fresh clone + actual ZIP + official runner; 900 is the full submission check.
set -euo pipefail
umask 0002
root=$(cd "$(dirname "$0")/../.." && pwd)
archive=$(realpath "${1:?Usage: selfcheck.sh ZIP RUN_ID [SECONDS]}")
run_id=${2:?Provide unique run ID}
seconds=${3:-900}
[[ "$run_id" =~ ^[a-zA-Z0-9_-]+$ ]] || { printf 'Unsafe run ID\n' >&2; exit 2; }
checkout="$root/output/selfcheck/$run_id"
mkdir -p "$root/output/selfcheck"
git clone https://github.com/leonyoon-3dai/PhyRC_2027_phase1.git "$checkout"
git -C "$checkout" checkout --detach 9d978072c0064f01fe13243def30c2766602e86d
mkdir "$checkout/participant"
python3 - "$archive" "$checkout/participant" <<'PY'
import hashlib,json,sys,zipfile
from pathlib import Path
archive,destination=map(Path,sys.argv[1:])
with zipfile.ZipFile(archive) as z:
    for item in z.infolist():
        if item.is_dir():continue
        p=(destination/item.filename).resolve()
        if destination.resolve() not in p.parents:raise ValueError('unsafe ZIP path')
    z.extractall(destination)
manifest=json.loads((destination/'SHA256.json').read_text())
for name,expected in manifest.items():
    with (destination/name).open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
    if actual!=expected:raise ValueError('extracted checksum mismatch '+name)
print('ZIP extraction checksum pass')
PY
cd "$checkout"
./run.sh doctor > doctor.log 2>&1
./run.sh prepare > prepare.log 2>&1
docker build -t "phyrc-selfcheck:$run_id" participant > build.log 2>&1
docker image inspect "phyrc-selfcheck:$run_id" --format '{{.Id}} {{json .RepoDigests}}' > image-digest.txt
git rev-parse HEAD > source-commit.txt
PHYRC_IMAGE="phyrc-selfcheck:$run_id" ./run.sh python /scripts/evaluate_policy.py \
  --policy /project/participant/policy.py --seeds 42 --seconds "$seconds" \
  --output /output/evaluation/submission_check
