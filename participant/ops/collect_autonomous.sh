#!/usr/bin/env bash
# Run one fresh GPT collection, then validate the closed capture and export its gallery.
set -euo pipefail
cd "$(dirname "$0")/../.."
umask 027
if [[ ! ${1:-} =~ ^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,119}$ ]]; then
    echo 'Usage: participant/ops/collect_autonomous.sh NEW_RUN_ID [--sol-max|--sol-ultra] [--camera-briefing] [--gentle-wrist-dressing] [--wrist-transfer-from RUN STEP] [--cover-right-wrist] [--gpt-task-prompt FILE]' >&2
    exit 2
fi
run=$1
shift
model=gpt-6.2-astra
effort=ultra
options=()
reset=(--seed 43)
segment_decisions=3
while (( $# )); do
    case "$1" in
        --sol-max) model=gpt-6.2-sol; effort=max ;;
        --sol-ultra) model=gpt-6.2-sol; effort=ultra ;;
        --camera-briefing|--gentle-wrist-dressing) options+=("$1") ;;
        --cover-right-wrist) options+=("$1"); segment_decisions=1 ;;
        --gpt-task-prompt)
            if (( $# < 2 )); then echo 'Expected a task prompt file.' >&2; exit 2; fi
            options+=("$1" "$2")
            segment_decisions=1
            shift ;;
        --wrist-transfer-from)
            if (( $# < 3 )); then echo 'Expected a source run and a replay step.' >&2; exit 2; fi
            options+=(--wrist-transfer --replay-prefix-run "$2" --replay-prefix-steps "$3")
            reset=()
            shift 2 ;;
        *) echo "Unknown collection option: $1" >&2; exit 2 ;;
    esac
    shift
done
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
    --run-id "$run" --mode dressing --gpt-only --until-full-score-or-feedback "${options[@]}" \
    --model "$model" --effort "$effort" --actor-backend exec --plan-size 1 \
    "${reset[@]}" --named-actions --wrist-depth-panel --segment-review-dir output/segment-review \
    --segment-decisions "$segment_decisions" --segment-steps 60 --post-action-settle-steps 0 \
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
