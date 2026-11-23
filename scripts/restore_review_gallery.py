"""Restore a closed series' SQLite journal and reviewed MP4s to a new gallery directory."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,119}')


def checked_file(directory, item):
    path = (directory / item['path']).resolve()
    path.relative_to(directory.resolve())
    with path.open('rb') as source:
        if path.stat().st_size != item['bytes'] or hashlib.file_digest(source, 'sha256').hexdigest() != item['sha256']:
            raise ValueError(f'Backup checksum mismatch: {path.name}')
    return path


def restore(manifest, directory, destination):
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f'Choose a new gallery directory: {destination}')
    journal = checked_file(directory, manifest['journal'])
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as tmp:
        staged = Path(tmp) / 'gallery'
        staged.mkdir(mode=0o700)
        db_path = staged / 'journal.sqlite3'
        shutil.copyfile(journal, db_path)
        with sqlite3.connect(db_path.resolve().as_uri() + '?mode=ro', uri=True) as db:
            if db.execute('PRAGMA integrity_check').fetchone() != ('ok',):
                raise ValueError('Invalid review database')
            digest_rows = list(db.execute('SELECT run,segment,digest FROM segments ORDER BY rowid'))
        runs = {row['run_id']: row for row in manifest['runs']}
        if set(runs) != {run for run, _, _ in digest_rows}:
            raise ValueError('Journal runs differ from the backup receipt')
        for run, metadata in runs.items():
            if not ID.fullmatch(run):
                raise ValueError('Unexpected run ID')
            media = staged / 'media' / run
            media.mkdir(parents=True)
            with zipfile.ZipFile(checked_file(directory, metadata['review_zip'])) as archive:
                for stored_run, hold, digest in digest_rows:
                    if stored_run != run:
                        continue
                    if not ID.fullmatch(hold):
                        raise ValueError('Unexpected segment ID')
                    mp4 = media / (hold + '.mp4')
                    with archive.open(mp4.relative_to(staged).as_posix()) as source, mp4.open('xb') as output:
                        shutil.copyfileobj(source, output)
                    with mp4.open('rb') as f:
                        if hashlib.file_digest(f, 'sha256').hexdigest() != digest:
                            raise ValueError(f'Clip differs from the reviewed observation: {run}/{hold}')
        staged.rename(destination)
    return len(digest_rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt', type=Path, default=ROOT / 'docs/active/20261123-private-backup.json')
    parser.add_argument('--download-root', type=Path, help='Existing snapshot with the relative paths in the receipt')
    parser.add_argument('--destination', type=Path, default=ROOT / 'output/segment-review')
    args = parser.parse_args()
    receipt = json.loads(args.receipt.read_text())
    dest = args.destination.absolute()
    os.umask(0o077)
    if args.download_root:
        count = restore(receipt, args.download_root, dest)
    else:
        if dest.exists() or dest.is_symlink():
            parser.error('The destination already exists; choose a new directory')
        items = [receipt['journal'], *(r['review_zip'] for r in receipt['runs'])]
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(['hf', 'download', receipt['repo_id'], *(item['path'] for item in items),
                            '--repo-type', receipt['repo_type'], '--revision', receipt['revision'],
                            '--local-dir', tmp], check=True)
            count = restore(receipt, Path(tmp), dest)
    print(f'Restored {count} verified clips and the journal to {dest}')


if __name__ == '__main__':
    main()
