#!/usr/bin/env python3
"""Restore the two starting slots and the original prompts from pinned private backups."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    (25, 1200, '20261126-demo24-25-private-backup.json'),
    (26, 2905, '20261126-demo26-32-private-backup.json'),
)


def file_digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def source_members(run):
    name = run['run_id']
    trace = f'output/operator-traces/{name}'
    return {
        f'{trace}/prompt.txt', f'{trace}/attempt.json',
        f'output/collections/{name}/run_metadata.json',
    }


def verify_members(found, raw_manifest, run):
    name = run['run_id']
    trace = f'output/operator-traces/{name}'
    if hashlib.sha256(raw_manifest).hexdigest() != run['manifest_sha256']:
        raise ValueError(f'Archive manifest does not match pinned receipt: {name}')
    manifest = json.loads(raw_manifest)
    for key, payload in found.items():
        if manifest.get(key) != {'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest()}:
            raise ValueError(f'Archive member does not match pinned manifest: {key}')
    attempt = json.loads(found[f'{trace}/attempt.json'])
    if (attempt.get('run_id') != name or not attempt.get('finished')
            or attempt.get('prompt_sha256') != hashlib.sha256(found[f'{trace}/prompt.txt']).hexdigest()):
        raise ValueError(f'Prompt does not match the finished source attempt: {name}')


def read_archive(archive, run):
    targets = source_members(run) | {'SHA256.json'}
    found = {}
    with tarfile.open(archive, 'r|gz') as members:
        for member in members:
            if member.name not in targets:
                continue
            if member.name in found or not member.isfile() or not 0 < member.size <= 8 * 1024 * 1024:
                raise ValueError(f'Invalid source archive member: {member.name}')
            with members.extractfile(member) as stream:
                found[member.name] = stream.read()
            if found.keys() == targets:
                break
    if found.keys() != targets:
        raise ValueError(f'Missing source archive items: {sorted(targets - found.keys())}')
    raw_manifest = found.pop('SHA256.json')
    verify_members(found, raw_manifest, run)
    return found, raw_manifest


def publish(root, files):
    for name, content in files.items():
        path = root / name
        if any(parent.is_symlink() for parent in (path, *path.parents)):
            raise ValueError(f'Symlink in restore destination: {path}')
        if path.exists() and (not path.is_file() or path.read_bytes() != content):
            raise FileExistsError(f'Existing source differs from the pinned backup: {path}')
    for name, content in files.items():
        path = root / name
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent) as staged:
            os.fchmod(staged.fileno(), 0o640)
            staged.write(content)
            staged.flush()
            try:
                os.link(staged.name, path)
            except FileExistsError:
                if path.is_symlink() or not path.is_file() or path.read_bytes() != content:
                    raise


def restore(root, download, *, local_only):
    files = {}
    for number, step, filename in SOURCES:
        backup = json.loads((root / 'docs/active' / filename).read_text())
        run = next(row for row in backup['runs'] if row['demonstration'] == number)
        checkpoint = next(row for row in run['checkpoints'] if row['step'] == step)
        items = (checkpoint['slot'], checkpoint['receipt'], run['archive'])
        checkpoint_dir = Path(checkpoint['archive_member_prefix'])
        manifest_path = Path('output/demo33-34-sources') / f'demo{number}-manifest.json'
        existing = [root / (checkpoint_dir / Path(item['path']).name) for item in items[:2]]
        if all(path.is_file() for path in [root / manifest_path, *existing,
                                         *(root / name for name in source_members(run))]):
            for path, item in zip(existing, items):
                if path.stat().st_size != item['bytes'] or file_digest(path) != item['sha256']:
                    raise ValueError(f'Existing source differs from the pinned backup: {path}')
            verify_members({name: (root / name).read_bytes() for name in source_members(run)},
                           (root / manifest_path).read_bytes(), run)
            print(f'Reused verified Demo {number}/{step} and the original prompt', flush=True)
            continue
        missing = [item['path'] for item in items if not (download / item['path']).is_file()]
        if missing and not local_only:
            print(f'Downloading missing pinned files for Demo {number}', flush=True)
            subprocess.run(['hf', 'download', backup['repo_id'], *missing,
                            '--repo-type', backup['repo_type'], '--revision', backup['revision'],
                            '--local-dir', str(download)], check=True, stdout=subprocess.DEVNULL)
        for item in items:
            path = download / item['path']
            if path.stat().st_size != item['bytes'] or file_digest(path) != item['sha256']:
                raise ValueError(f'Backup checksum mismatch: {item["path"]}')
        captured, manifest = read_archive(download / run['archive']['path'], run)
        for item in items[:2]:
            files[checkpoint_dir / Path(item['path']).name] = (download / item['path']).read_bytes()
        files.update(captured)
        files[manifest_path] = manifest
        print(f'Verified Demo {number}/{step} and the original prompt', flush=True)
    publish(root, files)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download-root', type=Path,
                        help='Use files already downloaded under this backup tree, with no network access')
    args = parser.parse_args()
    os.umask(0o027)
    try:
        restore(ROOT, (args.download_root or ROOT / '.runtime/demo33-34-backup').resolve(),
                local_only=args.download_root is not None)
    except (OSError, ValueError, KeyError, tarfile.TarError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f'Restore failed: {exc}\n')


if __name__ == '__main__':
    main()
