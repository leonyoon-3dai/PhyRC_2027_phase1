#!/usr/bin/env bash
# Run one fresh GPT collection, then validate the closed capture and export its gallery.
set -euo pipefail
cd "$(dirname "$0")/../.."
umask 027
if [[ $# != 1 || ! $1 =~ ^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,119}$ ]]; then
    echo 'Usage: participant/ops/collect_autonomous.sh NEW_RUN_ID' >&2
    exit 2
fi
run=$1
capture="output/collections/$run"
log="output/preflight/$run.log"
qc="output/preflight/$run-qc.log"
bundle="output/review-exports/$run.zip"
mkdir -p .runtime output/preflight output/collections output/operator-traces output/review-exports
exec 8>.runtime/autonomous-launch.lock
flock -n 8 || { echo 'An autonomous collection is already running here.' >&2; exit 1; }
for path in "$capture" "output/operator-traces/$run" "output/actors/$run" "$log" "$qc" "$bundle"; do
    if [[ -e $path ]]; then
        echo "Refusing to reuse $run, existing path $path" >&2
        exit 1
    fi
done
export PATH="$PWD/.runtime/codex-0.166.0/node_modules/.bin:$PATH"
export PYTHONPATH=.:src/PhyRC_Sim
python_bin=.venv/bin/python
# The simulator uses UID 1234 in the host user's group.
chmod g+rwx output output/collections
chmod g+rx output/operator-traces
printf '%s\n' "$run" > .runtime/active-autonomous-run.tmp
mv .runtime/active-autonomous-run.tmp .runtime/active-autonomous-run
client_status=0
"$python_bin" -m participant.collection.codex_client \
    --run-id "$run" --mode dressing --gpt-only \
    --model gpt-6.2-astra --effort ultra --actor-backend exec --plan-size 1 \
    --seed 43 --named-actions --wrist-depth-panel --segment-review-dir output/segment-review \
    --segment-decisions 3 --segment-steps 60 --post-action-settle-steps 0 \
    --max-steps 18000 --model-timeout 180 >"$log" 2>&1 || client_status=$?
if [[ -e "$capture/capture.json" ]]; then
    "$python_bin" -m participant.collection.validate_capture "$capture" --output "$capture/validation.json" >"$qc" 2>&1
    "$python_bin" tools/segment_review.py --root output/segment-review bundle --run "$run" \
        --collection "$capture" --out "$bundle" >>"$qc" 2>&1
elif [[ $client_status -eq 0 ]]; then
    echo 'Collector returned without a closed capture. See the run log.' >&2
    exit 1
fi
exit "$client_status"
