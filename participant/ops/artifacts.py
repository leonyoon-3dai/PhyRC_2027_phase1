#!/usr/bin/env python3
"""Explicit artifact-directory checksum manifest, validation and clean restore.

Only pack a reviewed artifact directory, never $HOME or the whole project.
Symlinks and credential-like paths are rejected. Upload is separate via hf CLI.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tarfile

MANIFEST = 'SHA256.json'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def inventory(root):
    values = {}
    for path in sorted(root.rglob('*')):
        name = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise ValueError('symlinks forbidden: '+name)
        if not path.is_file() or name == MANIFEST:
            continue
        if any(part.startswith('.env') or part in ('.git','.ssh','auth.json','token','stored_tokens') or part.endswith(('.pem','.key')) for part in path.relative_to(root).parts):
            raise ValueError('credential-like path forbidden: '+name)
        values[name] = {'bytes':path.stat().st_size, 'sha256':digest(path)}
    return values


def verify(root):
    recorded = json.loads((root/MANIFEST).read_text())
    actual = inventory(root)
    if not recorded or recorded != actual:
        raise ValueError('manifest mismatch or empty snapshot')
    return actual


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['manifest','verify','pack','restore'])
    p.add_argument('directory', type=Path)
    p.add_argument('--archive', type=Path)
    a = p.parse_args()
    root = a.directory.resolve()
    if a.command == 'manifest':
        manifest = root/MANIFEST
        with manifest.open('x') as f:
            json.dump(inventory(root),f,indent=2); f.write('\n')
    elif a.command == 'verify':
        verify(root)
    elif a.command == 'pack':
        verify(root)
        if a.archive is None or root in a.archive.resolve().parents:
            p.error('--archive must be outside artifact directory')
        with tarfile.open(a.archive,'x:gz') as tar:
            for path in sorted(root.rglob('*')):
                if path.is_file():
                    tar.add(path,arcname=path.relative_to(root),recursive=False)
        print('archive_sha256='+digest(a.archive))
    else:
        if a.archive is None or root.exists():
            p.error('restore requires archive and a new destination')
        root.mkdir(parents=True)
        try:
            with tarfile.open(a.archive,'r:gz') as tar:
                members = tar.getmembers()
                names = set()
                for member in members:
                    path = root/member.name
                    if not member.isfile() or path.resolve() == root or root not in path.resolve().parents or member.name in names:
                        raise ValueError('unsafe or duplicate archive member')
                    names.add(member.name)
                for member in members:
                    path = root/member.name
                    path.parent.mkdir(parents=True,exist_ok=True)
                    with tar.extractfile(member) as src, path.open('xb') as dst:
                        shutil.copyfileobj(src,dst)
            verify(root)
        except BaseException:
            # Retain failed restore for diagnosis; never remove an existing directory.
            raise
    print(json.dumps({'command':a.command,'directory':str(root),'verified':a.command!='manifest'}))

if __name__ == '__main__':
    main()
