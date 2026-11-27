#!/usr/bin/env python3
"""Restore pinned checkpoint and provenance files for the Demo 37/38 handoff."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

from restore_demo33_34_sources import publish


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = Path('docs/active/20261127-demo35-36-handoff-receipt.json')


def relative_path(value):
    if (not isinstance(value, str) or value.startswith('-') or '\\' in value
            or any(part in ('', '.', '..') for part in value.split('/'))):
        raise ValueError(f'Invalid relative path in the handoff receipt: {value!r}')
    return Path(value)


def validate_receipt(receipt):
    if (receipt['schema'] != 'phyrc-elbow-handoff-v1' or receipt['repo_type'] != 'dataset'
            or not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9._-]*/[A-Za-z0-9_][A-Za-z0-9._-]*', receipt['repo_id'])
            or not re.fullmatch(r'[0-9a-f]{40}', receipt['revision'])):
        raise ValueError('Invalid pinned handoff revision or dataset')
    if not isinstance(receipt['files'], list) or not receipt['files']:
        raise ValueError('The handoff receipt has no files')
    files = []
    destinations = set()
    for item in receipt['files']:
        source = relative_path(item['path'])
        destination = relative_path(item['destination'])
        if (destination.parts[0] != 'output' or len(destination.parts) < 2
                or destination in destinations or type(item['bytes']) is not int or item['bytes'] < 0
                or not re.fullmatch(r'[0-9a-f]{64}', item['sha256'])):
            raise ValueError(f'Invalid handoff file entry: {destination}')
        destinations.add(destination)
        files.append((source, destination, item))
    return files


def checked_bytes(path, item):
    if not path.is_file() or path.stat().st_size != item['bytes']:
        raise ValueError(f'File size or type differs from the pinned backup: {path}')
    payload = path.read_bytes()
    if len(payload) != item['bytes'] or hashlib.sha256(payload).hexdigest() != item['sha256']:
        raise ValueError(f'File hash differs from the pinned backup: {path}')
    return payload


def restore(root, download, *, local_only):
    receipt = json.loads((root / RECEIPT).read_text())
    files = validate_receipt(receipt)
    missing = []
    for source, destination, item in files:
        path = root / destination
        if any(part.is_symlink() for part in (path, *path.parents)):
            raise ValueError(f'Symlink in restore destination: {path}')
        if path.exists():
            checked_bytes(path, item)
        else:
            missing.append((source, destination, item))

    if missing and not local_only:
        paths = list(dict.fromkeys(source.as_posix() for source, _, _ in missing))
        subprocess.run(['hf', 'download', receipt['repo_id'], *paths,
                        '--repo-type', receipt['repo_type'], '--revision', receipt['revision'],
                        '--local-dir', str(download)], check=True, stdout=subprocess.DEVNULL)
    restored = {destination: checked_bytes(download / source, item)
                for source, destination, item in missing}
    publish(root, restored)
    print(f'Verified {len(files)} handoff files. Restored {len(restored)} missing files.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download-root', type=Path,
                        help='Use the existing HF-relative download tree without network access')
    args = parser.parse_args()
    os.umask(0o027)
    try:
        if args.download_root:
            restore(ROOT, args.download_root.resolve(), local_only=True)
        else:
            with tempfile.TemporaryDirectory(prefix='phyrc-elbow-handoff-') as directory:
                restore(ROOT, Path(directory), local_only=False)
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f'Restore failed: {exc}\n')


if __name__ == '__main__':
    main()
