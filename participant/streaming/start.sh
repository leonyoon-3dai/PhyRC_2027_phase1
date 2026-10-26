#!/usr/bin/env bash
set -euo pipefail
umask 0002
cd "$(dirname "$0")/../.."
: "${STRETCH4_STREAM_HOST:?Set advertised server IPv4; firewall must already restrict the streaming ports}"
sudo -n iptables -S PHYRC_STREAM >/dev/null
export STRETCH4_TRAINING_RECORD=1 STRETCH4_TRAINING_RENDER=deferred
request="/output/training_export_requests/$(date -u +%Y%m%dT%H%M%SZ)-stream-$$.json"
mkdir -p output/training_export_requests
chmod g+rwx output/training_export_requests
export STRETCH4_TRAINING_EXPORT_REQUEST="$request"
./run.sh python /scripts/stream_teleop.py
if [[ -f "output/${request#/output/}" ]]; then
    if [[ "${STRETCH4_DEFER_EXPORT:-0}" == 1 ]]; then
        printf 'Capture saved; RGBD export queued: %s\n' "$request"
        printf 'After collection, run: ./run.sh python /scripts/export_policy_dataset.py --request %q\n' "$request"
    else
        ./run.sh python /scripts/export_policy_dataset.py --request "$request"
    fi
else
    printf 'No completed capture request; inspect teleop logs and capture status.\n' >&2
    exit 1
fi
